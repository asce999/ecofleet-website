import datetime
from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult
from core.models import AttendanceWorkbook, AttendanceRecord

class AttendanceProvider(BaseProvider):
    category = "Business Modules"
    key = "attendance"
    title = "Attendance Module"
    summary = "Attendance sheet health and active configurations."
    cache_timeout = 60

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = []
        metrics = {}
        
        active = AttendanceWorkbook.objects.filter(is_active=True).first()
        if active:
            checks.append(CheckResult(name="Active Workbook", status="healthy", message="Loaded"))
            metrics["Active Month"] = active.uploaded_at.strftime("%B %Y") if active.uploaded_at else "Unknown"
        else:
            status = "warning"
            checks.append(CheckResult(name="Active Workbook", status="warning", message="None configured"))
            metrics["Active Month"] = "None"
            
        total_records = AttendanceRecord.objects.count()
        today = timezone.now().date()
        today_records = AttendanceRecord.objects.filter(record_date=today).count()
        unique_drivers = AttendanceRecord.objects.values('driver').distinct().count()
        
        metrics["Total Records"] = total_records
        metrics["Drivers Tracked"] = unique_drivers
        metrics["Today's Attendance"] = today_records
        
        if total_records == 0:
            status = "warning" if status == "healthy" else status
            checks.append(CheckResult(name="Records", status="warning", message="No attendance data found"))
        else:
            checks.append(CheckResult(name="Records", status="healthy", message="Data available"))

        return ProviderResult(
            status=status,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0),
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics
        )
