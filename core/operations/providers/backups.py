import os
import datetime
from django.conf import settings
from django.utils import timezone
from .base import BaseProvider
from core.models import SystemEvent

class BackupsProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "Backups"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics = {}
        
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            return {
                "status": "warning",
                "title": self.title,
                "summary": "Backup directory does not exist yet.",
                "checks": [{"name": "Directory", "status": "warning", "message": "Missing"}],
                "metrics": {"Total Backups": 0},
                "last_updated": timezone.now()
            }
            
        all_backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith('ecofleet_') and f.endswith('.sqlite3.gz')],
            reverse=True
        )
        
        metrics["Total Backups"] = len(all_backups)
        
        if not all_backups:
            status = "warning"
            checks.append({"name": "Recent Backup", "status": "warning", "message": "No backups found"})
            metrics["Latest Backup"] = "None"
        else:
            latest = all_backups[0]
            latest_path = os.path.join(backup_dir, latest)
            size_mb = os.path.getsize(latest_path) / (1024 * 1024)
            mtime = os.path.getmtime(latest_path)
            dt = datetime.datetime.fromtimestamp(mtime)
            
            metrics["Latest Backup"] = f"{latest} ({size_mb:.2f} MB)"
            metrics["Latest Date"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if backup is older than 24 hours
            if (datetime.datetime.now() - dt).total_seconds() > 86400:
                status = "warning"
                checks.append({"name": "Freshness", "status": "warning", "message": "> 24h old"})
            else:
                checks.append({"name": "Freshness", "status": "healthy", "message": "OK (< 24h)"})

        # Check for backup failures
        recent_failures = SystemEvent.objects.filter(
            event_type="Backup", 
            severity=SystemEvent.SEVERITY_CRITICAL,
            timestamp__gte=timezone.now() - datetime.timedelta(days=1)
        ).count()
        
        if recent_failures > 0:
            status = "critical"
            checks.append({"name": "Failures", "status": "critical", "message": f"{recent_failures} failures in 24h"})
            
        return {
            "status": status,
            "title": self.title,
            "summary": "Automated database backup status",
            "checks": checks,
            "metrics": metrics,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
