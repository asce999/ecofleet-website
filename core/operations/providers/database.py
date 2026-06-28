import os
from django.db import connection
from django.conf import settings
from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult

class DatabaseProvider(BaseProvider):
    category = "Infrastructure"
    key = "database"
    title = "Database"
    summary = "SQLite Database connectivity and metrics"

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = []
        metrics = {}
        
        try:
            connection.ensure_connection()
            checks.append(CheckResult(name="Connection", status="healthy", message="OK"))
        except Exception as e:
            status = "critical"
            checks.append(CheckResult(name="Connection", status="critical", message=str(e)))

        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            metrics["File Size"] = f"{size_mb:.2f} MB"
            if size_mb > 1024:
                status = "warning" if status != "critical" else "critical"
                checks.append(CheckResult(name="Size", status="warning", message="DB size > 1GB"))
        else:
            status = "critical"
            checks.append(CheckResult(name="File Exists", status="critical", message=f"{db_path} not found"))

        return ProviderResult(
            status=status,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0),
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics
        )
