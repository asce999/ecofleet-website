

import time
from django.core.cache import cache

class PerformanceMiddleware:
    """
    Tracks request latency and stores rolling metrics in the cache.
    Does not perform expensive DB writes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = (time.time() - start_time) * 1000

        # Ignore static and media paths
        if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            metrics = cache.get('performance_metrics', {
                'requests': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'slowest_endpoint': 'None',
                'recent_times': []
            })

            metrics['requests'] += 1
            metrics['total_time'] += duration_ms
            if duration_ms < metrics.get('min_time', float('inf')):
                metrics['min_time'] = duration_ms
            if duration_ms > metrics.get('max_time', 0.0):
                metrics['max_time'] = duration_ms
                metrics['slowest_endpoint'] = request.path
                
            # Maintain a rolling window of the last 200 requests for the 95th percentile
            metrics['recent_times'].append(duration_ms)
            if len(metrics['recent_times']) > 200:
                metrics['recent_times'].pop(0)

            # Store in cache
            cache.set('performance_metrics', metrics, timeout=None)

        return response
