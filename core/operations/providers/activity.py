from django.utils import timezone
from .base import BaseProvider
from core.models import SystemEvent
import datetime

class ActivityProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "System Activity"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics = {}
        
        one_day_ago = timezone.now() - datetime.timedelta(days=1)
        
        total_24h = SystemEvent.objects.filter(timestamp__gte=one_day_ago).count()
        info_24h = SystemEvent.objects.filter(timestamp__gte=one_day_ago, severity=SystemEvent.SEVERITY_INFO).count()
        warn_24h = SystemEvent.objects.filter(timestamp__gte=one_day_ago, severity=SystemEvent.SEVERITY_WARNING).count()
        crit_24h = SystemEvent.objects.filter(timestamp__gte=one_day_ago, severity=SystemEvent.SEVERITY_CRITICAL).count()
        
        metrics["Events (24h)"] = total_24h
        metrics["Info"] = info_24h
        metrics["Warnings"] = warn_24h
        metrics["Criticals"] = crit_24h
        
        if crit_24h > 0:
            status = "critical"
            checks.append({"name": "Critical Events", "status": "critical", "message": f"{crit_24h} in 24h"})
        elif warn_24h > 10:
            status = "warning"
            checks.append({"name": "Warning Events", "status": "warning", "message": f"{warn_24h} in 24h"})
        else:
            checks.append({"name": "Event Volume", "status": "healthy", "message": "Normal"})

        # Chart labels and datasets (Line chart showing last 24 hours of events in 6 intervals)
        labels = []
        info_data = []
        warn_data = []
        err_data = []
        
        now = timezone.now()
        for i in range(6):
            start = now - datetime.timedelta(hours=(6-i)*4)
            end = now - datetime.timedelta(hours=(5-i)*4)
            labels.append(start.strftime("%H:%M"))
            
            interval_info = SystemEvent.objects.filter(
                timestamp__gte=start, 
                timestamp__lt=end, 
                severity=SystemEvent.SEVERITY_INFO
            ).count()
            interval_warn = SystemEvent.objects.filter(
                timestamp__gte=start, 
                timestamp__lt=end, 
                severity=SystemEvent.SEVERITY_WARNING
            ).count()
            interval_crit = SystemEvent.objects.filter(
                timestamp__gte=start, 
                timestamp__lt=end, 
                severity=SystemEvent.SEVERITY_CRITICAL
            ).count()
            
            info_data.append(interval_info)
            warn_data.append(interval_warn)
            err_data.append(interval_crit)
            
        metrics["labels"] = labels
        metrics["datasets"] = [
            {"label": "Info", "data": info_data},
            {"label": "Warnings", "data": warn_data},
            {"label": "Errors", "data": err_data}
        ]

        return {
            "status": status,
            "title": self.title,
            "summary": "Recent system event activity logs.",
            "checks": checks,
            "metrics": metrics,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
