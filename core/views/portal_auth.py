from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)

def portal_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        # django-axes monitors failed authenticate() calls automatically
        # (AuthenticationForm.clean() invokes authenticate() under the hood)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                logger.warning(f"Failed login attempt by non-staff user: {user.username}")
                messages.error(request, "This account isn't authorised for the employee portal.")
            else:
                auth_login(request, user)
                logger.info(f"Successful login: {user.username}")
                nxt = request.POST.get('next') or request.GET.get('next')
                if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
                    return redirect(nxt)
                return redirect('dashboard')
        else:
            username = request.POST.get('username', 'unknown')
            logger.warning(f"Failed login attempt for username: {username}")
            messages.error(request, "Invalid username or password.")

    return render(request, 'core/portal/login.html', {'form': form})


@require_POST
def portal_logout(request):
    user = request.user.username if request.user.is_authenticated else 'unknown'
    auth_logout(request)
    logger.info(f"Logout: {user}")
    messages.success(request, "You've been logged out.")
    return redirect('portal_login')


