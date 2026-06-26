import os
from django.http import FileResponse, Http404
from django.conf import settings
from core.decorators import staff_required

@staff_required
def protected_media(request, path):
    """
    Serve media files only to authenticated staff users.
    Uses X-Accel-Redirect if NGINX_ACCEL_REDIRECT is True in settings,
    otherwise streams directly via FileResponse (for local dev).
    """
    full_path = os.path.join(settings.MEDIA_ROOT, path)

    # Prevent path traversal
    media_root = os.path.realpath(settings.MEDIA_ROOT)
    requested = os.path.realpath(full_path)
    if not requested.startswith(media_root):
        raise Http404

    if not os.path.isfile(requested):
        raise Http404

    if getattr(settings, 'NGINX_ACCEL_REDIRECT', False):
        # Let Nginx serve the file efficiently after Django auth check
        response = FileResponse(open(requested, 'rb'))
        response['X-Accel-Redirect'] = '/protected-media/' + path
        response['Content-Type'] = ''  # Let Nginx set this
        return response

    return FileResponse(open(requested, 'rb'))
