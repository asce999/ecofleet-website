from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult
from core.models import ToolRun

class FTLProvider(BaseProvider):
    category = "Business Modules"
    key = "ftl"
    title = "FTL Module"
    summary = "FTL generation health and metrics."

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = [CheckResult(name="Service", status="healthy", message="Available")]
        metrics = {}
        
        from core.models import FtlWorkbook
        total = ToolRun.objects.filter(tool='FTL Generator').count()
        metrics["Total Runs"] = total
        recent = ToolRun.objects.filter(tool='FTL Generator').order_by('-created_at').first()
        if recent:
            metrics["Last Run"] = recent.created_at.strftime("%Y-%m-%d %H:%M:%S")

        active_workbooks = FtlWorkbook.objects.filter(is_active=True).count()
        total_workbooks = FtlWorkbook.objects.count()
        metrics["Active Workbooks"] = active_workbooks
        metrics["Total Workbooks"] = total_workbooks

        return ProviderResult(
            status=status,
            health_score=100 if status == "healthy" else 0,
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics
        )
