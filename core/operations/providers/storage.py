import os
from django.conf import settings
from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult

class StorageProvider(BaseProvider):
    category = "Storage & Backups"
    key = "storage"
    title = "Storage & Media"
    summary = "File storage, static assets, and media."

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = []
        metrics = {}
        
        # Check media directory
        media_path = settings.MEDIA_ROOT
        if os.path.exists(media_path) and os.access(media_path, os.W_OK):
            checks.append(CheckResult(name="Media Directory Writable", status="healthy", message="OK"))
            
            # Count files and size
            total_size = 0
            file_count = 0
            for dirpath, _, filenames in os.walk(media_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
                        file_count += 1
            
            metrics["Media Files"] = file_count
            metrics["Media Size"] = f"{total_size / (1024*1024):.2f} MB"
        else:
            status = "critical"
            checks.append(CheckResult(name="Media Directory", status="critical", message="Missing or Read-Only"))

        # Static Directory
        static_path = settings.STATIC_ROOT or (settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
        if static_path and os.path.exists(static_path):
            checks.append(CheckResult(name="Static Directory", status="healthy", message="OK"))
        else:
            if settings.DEBUG:
                checks.append(CheckResult(name="Static Directory", status="warning", message="Missing (Ignored in dev)"))
            else:
                status = "warning"
                checks.append(CheckResult(name="Static Directory", status="warning", message="Missing in production"))
                
        # Server Disk Space (Windows)
        import shutil
        total, used, free = shutil.disk_usage(settings.BASE_DIR)
        metrics["Disk Total"] = f"{total / (1024**3):.2f} GB"
        metrics["Disk Free"] = f"{free / (1024**3):.2f} GB"
        
        # If less than 10% free, warning
        if (free / total) < 0.1:
            status = "critical" if status == "critical" else "warning"
            checks.append(CheckResult(name="Disk Space", status="warning", message="< 10% free space"))
        else:
            checks.append(CheckResult(name="Disk Space", status="healthy", message="OK"))

        # Chart labels and data (Doughnut)
        metrics["labels"] = ["Used Space (GB)", "Free Space (GB)"]
        metrics["data"] = [
            round(used / (1024**3), 2),
            round(free / (1024**3), 2)
        ]

        return ProviderResult(
            status=status,
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0)
        )
