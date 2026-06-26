from django.utils import timezone
from .base import BaseProvider
from core.models import AttendanceWorkbook, ToolRun

class AttendanceProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "Attendance Module"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics = {}
        
        active = AttendanceWorkbook.objects.filter(is_active=True).first()
        if active:
            checks.append({"name": "Active Workbook", "status": "healthy", "message": "Loaded"})
            metrics["Active Month"] = active.uploaded_at.strftime("%B %Y") if active.uploaded_at else "Unknown"
            # It seems portal_users does not exist or we shouldn't assume it does. 
            # If it fails, base provider will catch it. 
            metrics["Employees"] = active.portal_users.count() if hasattr(active, 'portal_users') else "N/A"
        else:
            status = "warning"
            checks.append({"name": "Active Workbook", "status": "warning", "message": "None configured"})
            metrics["Active Month"] = "None"

        return {
            "status": status,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "title": self.title,
            "summary": "Attendance sheet health and active configurations.",
            "checks": checks,
            "metrics": metrics,
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
