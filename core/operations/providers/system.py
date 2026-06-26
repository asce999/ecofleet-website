import sys
from django.conf import settings
from django.utils import timezone
from .base import BaseProvider
import django

class SystemProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "System Health"

    def _fetch_data(self):
        status = "healthy"
        
        metrics = {
            "Django Version": django.get_version(),
            "Python Version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "Environment": getattr(settings, 'ENVIRONMENT', 'development'),
            "Debug Mode": str(settings.DEBUG)
        }
        
        checks = []
        if settings.DEBUG:
            checks.append({"name": "Production Settings", "status": "warning", "message": "DEBUG is True"})
            if metrics["Environment"] == "production":
                status = "warning"
        else:
            checks.append({"name": "Production Settings", "status": "healthy", "message": "DEBUG is False"})

        return {
            "status": status,
            "title": self.title,
            "summary": "Core application framework health",
            "checks": checks,
            "metrics": metrics,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
