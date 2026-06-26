from django.utils import timezone
from django.conf import settings
from .base import BaseProvider
from core.models import ToolRun
import os

class COFProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "COF Module"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics = {}
        
        # Check letterhead
        lh_path = settings.COF_LETTERHEAD_PATH
        if os.path.exists(lh_path):
            checks.append({"name": "Letterhead", "status": "healthy", "message": "OK"})
        else:
            status = "critical"
            checks.append({"name": "Letterhead", "status": "critical", "message": "Missing"})

        total = ToolRun.objects.filter(tool='COF Generator').count()
        metrics["Total Runs"] = total
        recent = ToolRun.objects.filter(tool='COF Generator').order_by('-created_at').first()
        if recent:
            metrics["Last Run"] = recent.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "status": status,
            "health_score": 100 if status == "healthy" else 0,
            "title": self.title,
            "summary": "COF generator health and assets.",
            "checks": checks,
            "metrics": metrics,
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
