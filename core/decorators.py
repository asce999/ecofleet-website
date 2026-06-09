from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def staff_required(view_func):
    """Allow only authenticated staff (employees) into the portal."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        if request.user.is_authenticated:
            messages.error(request, "Your account isn't authorised for the employee portal.")
            return redirect('portal_login')
        login_url = reverse('portal_login')
        return redirect(f"{login_url}?{urlencode({'next': request.get_full_path()})}")
    return _wrapped
