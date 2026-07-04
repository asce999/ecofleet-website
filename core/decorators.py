from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def staff_required(view_func):
    """Allow only authenticated staff (employees) into the portal."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        if request.user.is_authenticated:
            logger.warning(f"Unauthorized staff access attempt by user: {request.user.username} to path: {request.path}")
            messages.error(request, "Your account isn't authorised for the employee portal.")
            return redirect('portal_login')
        return redirect(f"{reverse('portal_login')}?{urlencode({'next': request.get_full_path()})}")
    return _wrapped


def tool_permission_required(tool_name):
    """Enforce tool permissions based on UserProfile."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('portal_login')
            if not request.user.is_staff:
                logger.warning(f"Unauthorized tool access attempt by non-staff user: {request.user.username} for tool: {tool_name}")
                messages.error(request, "Your account isn't authorised for the employee portal.")
                return redirect('portal_login')
            
            from core.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            allowed = getattr(profile, f"can_use_{tool_name}", False)
            if not allowed:
                logger.warning(f"Permission denied: User '{request.user.username}' attempted to access unauthorized tool '{tool_name}' (IDOR/Escalation block)")
                messages.error(request, f"You do not have permission to access the {tool_name.replace('_', ' ').title()} tool.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def director_required(view_func):
    """Allow only users with Director role."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('portal_login')
        if not request.user.is_staff:
            logger.warning(f"Unauthorized director access attempt by non-staff user: {request.user.username}")
            messages.error(request, "Your account isn't authorised for the employee portal.")
            return redirect('portal_login')
        
        from core.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if profile.role != UserProfile.ROLE_DIRECTOR:
            logger.warning(f"Director-only access violation: User '{request.user.username}' (Role: {profile.role}) attempted to access path: {request.path}")
            messages.error(request, "Only the Director can access this section.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped
