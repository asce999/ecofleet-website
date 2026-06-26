from django.conf import settings
from django.utils import timezone
from .base import BaseProvider
from core.models import SystemEvent
import datetime

class SecurityProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "Security"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics = {}
        
        # Check security headers
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            if not settings.DEBUG:
                status = "warning"
                checks.append({"name": "SSL Redirect", "status": "warning", "message": "Disabled"})
            else:
                checks.append({"name": "SSL Redirect", "status": "warning", "message": "Disabled (Dev)"})
        else:
            checks.append({"name": "SSL Redirect", "status": "healthy", "message": "Enabled"})
            
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            if not settings.DEBUG:
                status = "warning"
                checks.append({"name": "Secure Cookies", "status": "warning", "message": "Disabled"})
            else:
                checks.append({"name": "Secure Cookies", "status": "warning", "message": "Disabled (Dev)"})
        else:
            checks.append({"name": "Secure Cookies", "status": "healthy", "message": "Enabled"})

        # Check for recent critical security events
        recent_security_events = SystemEvent.objects.filter(
            event_type="Security", 
            severity__in=[SystemEvent.SEVERITY_WARNING, SystemEvent.SEVERITY_CRITICAL],
            timestamp__gte=timezone.now() - datetime.timedelta(days=1)
        ).count()
        
        metrics["Events (24h)"] = recent_security_events
        
        if recent_security_events > 0:
            status = "warning" if status != "critical" else "critical"
            checks.append({"name": "Recent Threats", "status": "warning", "message": f"{recent_security_events} alerts logged"})
            
        return {
            "status": status,
            "title": self.title,
            "summary": "Application security settings and alerts.",
            "checks": checks,
            "metrics": metrics,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
