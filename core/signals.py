from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from core.models import UserProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance)

from django.contrib.auth.signals import user_logged_in, user_login_failed
from axes.signals import user_locked_out
import logging
from core.models import SystemEvent

logger = logging.getLogger(__name__)

def _get_request_id(request):
    return getattr(request, 'request_id', None) if request else None

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    try:
        SystemEvent.objects.create(
            component='auth',
            event_type='user_login',
            title='User Logged In',
            message=f"User {user.username} logged in successfully.",
            request_id=_get_request_id(request),
            user=user
        )
    except Exception as e:
        logger.error(f"Failed to log SystemEvent for user_logged_in: {e}")

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    try:
        SystemEvent.objects.create(
            severity=SystemEvent.SEVERITY_WARNING,
            component='auth',
            event_type='login_failed',
            title='Failed Login Attempt',
            message=f"Failed login attempt for username: {credentials.get('username', 'unknown')}",
            request_id=_get_request_id(request),
            metadata={'ip_address': request.META.get('REMOTE_ADDR') if request else 'unknown'}
        )
    except Exception as e:
        logger.error(f"Failed to log SystemEvent for user_login_failed: {e}")

@receiver(user_locked_out)
def log_user_locked_out(sender, request, username, ip_address, **kwargs):
    try:
        SystemEvent.objects.create(
            severity=SystemEvent.SEVERITY_CRITICAL,
            component='auth',
            event_type='user_locked_out',
            title='Account Locked Out',
            message=f"Account locked out for username: {username} from IP: {ip_address}",
            request_id=_get_request_id(request),
            metadata={'ip_address': ip_address, 'username': username}
        )
    except Exception as e:
        logger.error(f"Failed to log SystemEvent for user_locked_out: {e}")

