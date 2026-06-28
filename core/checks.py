import os
from django.conf import settings
from django.core.checks import Error, Warning, register

@register()
def check_log_directory(app_configs, **kwargs):
    errors = []
    log_dir = getattr(settings, 'LOGS_DIR', None)
    if not log_dir:
        return []
        
    if not os.path.exists(log_dir):
        errors.append(Error(
            f"Log directory {log_dir} does not exist.",
            id="core.E001"
        ))
    elif not os.access(log_dir, os.W_OK):
        errors.append(Error(
            f"Log directory {log_dir} is not writable.",
            id="core.E002"
        ))
    return errors

@register()
def check_media_directory(app_configs, **kwargs):
    errors = []
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        return []
        
    if not os.path.exists(media_root):
        errors.append(Warning(
            f"Media directory {media_root} does not exist. Uploads may fail.",
            id="core.W001"
        ))
    elif not os.access(media_root, os.W_OK):
        errors.append(Error(
            f"Media directory {media_root} is not writable.",
            id="core.E003"
        ))
    return errors
