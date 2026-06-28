import sys
from django.conf import settings
from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult
import django

class SystemProvider(BaseProvider):
    category = "Infrastructure"
    key = "system"
    title = "System Health"
    summary = "Core application framework health"

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        
        metrics = {
            "Django Version": django.get_version(),
            "Python Version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "Environment": getattr(settings, 'ENVIRONMENT', 'development'),
            "Debug Mode": str(settings.DEBUG)
        }
        
        checks = []
        if settings.DEBUG:
            checks.append(CheckResult(name="Production Settings", status="warning", message="DEBUG is True"))
            if metrics["Environment"] == "production":
                status = "warning"
        else:
            checks.append(CheckResult(name="Production Settings", status="healthy", message="DEBUG is False"))

        return ProviderResult(
            status=status,
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0)
        )
