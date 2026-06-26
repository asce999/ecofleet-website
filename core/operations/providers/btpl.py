from django.utils import timezone
from .base import BaseProvider
from core.models import ToolRun

class BTPLProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "BTPL Module"

    def _fetch_data(self):
        status = "healthy"
        checks = [{"name": "Service", "status": "healthy", "message": "Available"}]
        metrics = {}
        
        total = ToolRun.objects.filter(tool='BTPL Generator').count()
        metrics["Total Runs"] = total
        recent = ToolRun.objects.filter(tool='BTPL Generator').order_by('-created_at').first()
        if recent:
            metrics["Last Run"] = recent.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "status": status,
            "health_score": 100 if status == "healthy" else 0,
            "title": self.title,
            "summary": "BTPL generation health and metrics.",
            "checks": checks,
            "metrics": metrics,
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
