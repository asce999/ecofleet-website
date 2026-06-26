import os
from django.db import connection
from django.conf import settings
from django.utils import timezone
from .base import BaseProvider

class DatabaseProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "Database"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics = {}
        
        # Check connection
        try:
            connection.ensure_connection()
            checks.append({"name": "Connection", "status": "healthy", "message": "OK"})
        except Exception as e:
            status = "critical"
            checks.append({"name": "Connection", "status": "critical", "message": str(e)})

        # Check DB file size (SQLite specific)
        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            metrics["File Size"] = f"{size_mb:.2f} MB"
            if size_mb > 1024:  # > 1GB warns
                status = "warning" if status != "critical" else "critical"
                checks.append({"name": "Size", "status": "warning", "message": "DB size > 1GB"})
        else:
            status = "critical"
            checks.append({"name": "File Exists", "status": "critical", "message": f"{db_path} not found"})

        return {
            "status": status,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "title": self.title,
            "summary": "SQLite Database connectivity and metrics",
            "checks": checks,
            "metrics": metrics,
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
