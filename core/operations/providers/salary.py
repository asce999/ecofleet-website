from django.utils import timezone
from .base import BaseProvider
from core.models import SalaryConfig

class SalaryProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "Salary Module"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics = {}
        
        config = SalaryConfig.objects.first()
        if config:
            checks.append({"name": "Configuration", "status": "healthy", "message": "Loaded"})
            metrics["Base Per Day"] = f"₹{config.basic_rate_per_day}" if config.basic_rate_per_day else "N/A"
            metrics["SP Allow Per Day"] = f"₹{config.sp_allowance_rate_per_day}" if config.sp_allowance_rate_per_day else "N/A"
        else:
            status = "warning"
            checks.append({"name": "Configuration", "status": "warning", "message": "Missing defaults"})

        return {
            "status": status,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "title": self.title,
            "summary": "Salary calculation settings and health.",
            "checks": checks,
            "metrics": metrics,
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
