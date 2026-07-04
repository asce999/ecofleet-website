import os
import datetime
from django.conf import settings
from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult
from core.models import SystemEvent

class BackupsProvider(BaseProvider):
    category = "Storage & Backups"
    key = "backups"
    title = "Backups"
    summary = "Automated database backup status"

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = []
        metrics = {}
        
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            return ProviderResult(
                status="warning",
                title=self.title,
                summary="Backup directory does not exist yet.",
                checks=[CheckResult(name="Directory", status="warning", message="Missing")],
                metrics={"Total Backups": 0},
                health_score=80
            )
            
        all_backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith('ecofleet_') and (f.endswith('.sqlite3.gz') or f.endswith('.sql.gz'))],
            reverse=True
        )
        
        metrics["Total Backups"] = len(all_backups)
        
        if not all_backups:
            status = "warning"
            checks.append(CheckResult(name="Recent Backup", status="warning", message="No backups found"))
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
                checks.append(CheckResult(name="Freshness", status="warning", message="> 24h old"))
            else:
                checks.append(CheckResult(name="Freshness", status="healthy", message="OK (< 24h)"))

        # Check for backup failures in the last 24h
        recent_failures = SystemEvent.objects.filter(
            message__icontains="Backup", 
            severity=SystemEvent.SEVERITY_CRITICAL,
            timestamp__gte=timezone.now() - datetime.timedelta(days=1)
        ).count()
        
        if recent_failures > 0:
            status = "critical"
            checks.append(CheckResult(name="Failures", status="critical", message=f"{recent_failures} failures in 24h"))
            
        return ProviderResult(
            status=status,
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0)
        )
