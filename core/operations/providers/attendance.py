from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult
from core.models import AttendanceWorkbook, ToolRun

class AttendanceProvider(BaseProvider):
    category = "Business Modules"
    key = "attendance"
    title = "Attendance Module"
    summary = "Attendance sheet health and active configurations."

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = []
        metrics = {}
        
        active = AttendanceWorkbook.objects.filter(is_active=True).first()
        if active:
            checks.append(CheckResult(name="Active Workbook", status="healthy", message="Loaded"))
            metrics["Active Month"] = active.uploaded_at.strftime("%B %Y") if active.uploaded_at else "Unknown"
            metrics["Employees"] = active.portal_users.count() if hasattr(active, 'portal_users') else "N/A"
        else:
            status = "warning"
            checks.append(CheckResult(name="Active Workbook", status="warning", message="None configured"))
            metrics["Active Month"] = "None"

        return ProviderResult(
            status=status,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0),
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics
        )
