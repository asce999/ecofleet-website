from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult
from core.models import ToolRun

class BTPLProvider(BaseProvider):
    category = "Business Modules"
    key = "btpl"
    title = "BTPL Module"
    summary = "BTPL generation health and metrics."

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = [CheckResult(name="Service", status="healthy", message="Available")]
        metrics = {}
        
        total = ToolRun.objects.filter(tool='BTPL Generator').count()
        metrics["Total Runs"] = total
        recent = ToolRun.objects.filter(tool='BTPL Generator').order_by('-created_at').first()
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
