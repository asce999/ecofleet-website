from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib import messages
from django.utils.html import strip_tags
from django.core.cache import cache
from django.core import signing
import time
import logging
from core.models import Pincode

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'core/home.html')


def services(request):
    return render(request, 'core/services.html')


def get_client_ip(request):
    """
    Railway (and most PaaS providers) sit behind a reverse proxy, so
    REMOTE_ADDR is the proxy's internal IP, not the visitor's. The real
    client IP is the first entry in X-Forwarded-For (leftmost = original
    client; later entries are proxies it passed through).
    Falls back to REMOTE_ADDR for local dev where no proxy is present.
    """
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def contact(request):
    if request.method == 'POST':
        # 1. IP Rate Limiting
        client_ip = get_client_ip(request)
        cache_key = f'contact_form_ip_{client_ip}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 3:
            messages.error(request, "You have submitted too many requests. Please try again later.")
            return redirect('contact')
            
        # 2. Honeypot check
        honeypot = request.POST.get('website_url', '').strip()
        if honeypot:
            # Bot detected, silently discard
            return redirect('contact')

        # 2b. Time-based check — reject submissions faster than 3 seconds
        try:
            rendered_at = signing.loads(request.POST.get('_ts', ''), max_age=86400)
            if time.time() - rendered_at < 3:
                return redirect('contact')  # ponytail: too fast, likely bot
        except (signing.BadSignature, signing.SignatureExpired):
            return redirect('contact')  # missing or tampered token
            
        # 3. Extract and sanitize
        name = strip_tags(request.POST.get('name', '')).strip()
        company = strip_tags(request.POST.get('company', '')).strip()
        phone = strip_tags(request.POST.get('phone', '')).strip()
        email = strip_tags(request.POST.get('email', '')).strip()
        message = strip_tags(request.POST.get('message', '')).strip()
        
        if not all([name, phone, email, message]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('contact')
            
        # Strip newlines from subject to prevent header injection
        subject = f"New Contact Request from {name}"
        subject = "".join(subject.splitlines())
        
        body = f"""
New Contact Form Submission:

Name: {name}
Company: {company}
Phone: {phone}
Email: {email}

Message:
{message}
"""
        try:
            from django.conf import settings
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                ['info@ecofleetexpress.com'],
                fail_silently=False,
            )
            
            # Increment rate limit counter
            cache.set(cache_key, attempts + 1, timeout=3600)  # 1 hour timeout
            
            messages.success(request, "Thank you! Your message has been sent successfully. We will get back to you within 24 hours.")
            return redirect('contact')
        except Exception as e:
            logger.error(f"Error sending contact email: {e}")
            messages.error(request, "An error occurred while sending your message. Please try again later.")
            return redirect('contact')
            
    return render(request, 'core/contact.html', {'_ts': signing.dumps(time.time())})


def about(request):
    return render(request, 'core/about.html')


def privacy(request):
    return render(request, 'core/privacy.html')


def sitemap(request):
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ecofleetexpress.com/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://ecofleetexpress.com/about/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ecofleetexpress.com/services/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://ecofleetexpress.com/contact/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://ecofleetexpress.com/privacy/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>'''
    return HttpResponse(xml_content, content_type='application/xml')


def find_location(request):
    result = None
    pincode = request.GET.get('pincode', '').strip()

    if pincode:
        try:
            pin_obj = Pincode.objects.get(pin=pincode)
            result = {
                'found': True,
                'pin': pin_obj.pin,
                'city': pin_obj.city,
                'state': pin_obj.state,
                'location_type': pin_obj.location_type,
            }
        except Pincode.DoesNotExist:
            result = {'found': False}

    return render(request, 'core/find_location.html', {'result': result, 'pincode': pincode})


