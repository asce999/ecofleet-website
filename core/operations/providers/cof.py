from django.utils import timezone
from django.conf import settings
from .base import BaseProvider, ProviderResult, CheckResult
from core.models import ToolRun
import os

class COFProvider(BaseProvider):
    category = "Business Modules"
    key = "cof"
    title = "COF Module"
    summary = "COF generator health and assets."

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = []
        metrics = {}
        
        # Check letterhead
        lh_path = settings.COF_LETTERHEAD_PATH
        if os.path.exists(lh_path):
            checks.append(CheckResult(name="Letterhead", status="healthy", message="OK"))
        else:
            status = "critical"
            checks.append(CheckResult(name="Letterhead", status="critical", message="Missing"))

        total = ToolRun.objects.filter(tool='COF Generator').count()
        metrics["Total Runs"] = total
        recent = ToolRun.objects.filter(tool='COF Generator').order_by('-created_at').first()
        if recent:
            metrics["Last Run"] = recent.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return ProviderResult(
            status=status,
            health_score=100 if status == "healthy" else 0,
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics
        )
