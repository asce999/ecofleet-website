import os
import django
from django.conf import settings
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError
from django.core.cache import cache
from django.urls import reverse

from django.utils import timezone
from core.decorators import staff_required

def health_check(request):
    status = {
        'status': 'ok',
        'components': {
            'django': 'ok',
            'database': 'unknown',
            'media': 'unknown',
            'static': 'unknown'
        }
    }

    # 1. Database
    try:
        connection.ensure_connection()
        status['components']['database'] = 'ok'
    except OperationalError:
        status['components']['database'] = 'error'
        status['status'] = 'error'

    # 2. Media Directory
    media_path = settings.MEDIA_ROOT
    if os.path.exists(media_path) and os.access(media_path, os.W_OK):
        status['components']['media'] = 'ok'
    else:
        status['components']['media'] = 'error'
        status['status'] = 'error'

    # 3. Static Directory
    static_path = settings.STATIC_ROOT
    if not static_path:
        static_path = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None
    
    if static_path and os.path.exists(static_path):
        status['components']['static'] = 'ok'
    else:
        # In development STATIC_ROOT might not exist yet, so we just warn or ok if DIRS exists
        status['components']['static'] = 'warning'



    # Final response
    http_status = 200 if status['status'] == 'ok' else 503
    return JsonResponse(status, status=http_status)


@staff_required
def sentry_debug(request):
    if not settings.DEBUG:
        from django.http import Http404
        raise Http404("Not found")
    
    # This will trigger an unhandled exception for Sentry to capture
    division_by_zero = 1 / 0
    return JsonResponse({"status": "unreachable"})


