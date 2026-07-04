import time
import logging
import uuid
import threading
from django.core.cache import cache
from django.urls import resolve, Resolver404

logger = logging.getLogger(__name__)

_thread_locals = threading.local()

def get_current_request_id():
    return getattr(_thread_locals, "request_id", "-")

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_current_request_id()
        return True

class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request.request_id = request_id
        _thread_locals.request_id = request_id

        try:
            response = self.get_response(request)
        finally:
            if hasattr(_thread_locals, 'request_id'):
                del _thread_locals.request_id
        
        response['X-Request-ID'] = request_id
        return response


class PerformanceMiddleware:
    """
    Tracks request latency and stores metrics in the cache.
    Does not perform expensive DB writes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = (time.time() - start_time) * 1000

        if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            try:
                resolved = resolve(request.path)
                endpoint = resolved.view_name
            except Resolver404:
                endpoint = 'unknown'

            try:
                # Atomic increments
                cache.get_or_set(f"perf:count:{endpoint}", 0, timeout=None)
                cache.incr(f"perf:count:{endpoint}", delta=1)

                cache.get_or_set(f"perf:total_time:{endpoint}", 0, timeout=None)
                cache.incr(f"perf:total_time:{endpoint}", delta=int(duration_ms))
                
                # Min/Max (Acceptable race condition for observability)
                max_time = cache.get(f"perf:max:{endpoint}", 0.0)
                if duration_ms > max_time:
                    cache.set(f"perf:max:{endpoint}", duration_ms, timeout=None)
                    
                min_time = cache.get(f"perf:min:{endpoint}", float('inf'))
                if duration_ms < min_time:
                    cache.set(f"perf:min:{endpoint}", duration_ms, timeout=None)

            except Exception as e:
                # Fallback silently if Redis drops
                pass

        return response
