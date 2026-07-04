import os
from django.db import connection
from django.conf import settings
from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult

class DatabaseProvider(BaseProvider):
    category = "Infrastructure"
    key = "database"
    title = "Database"
    summary = "Database connectivity and metrics"
    cache_timeout = 60

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
            return ProviderResult(status=status, health_score=0, title=self.title, summary=self.summary, checks=checks, metrics=metrics)

        db_engine = settings.DATABASES['default']['ENGINE']
        db_name = settings.DATABASES['default']['NAME']

        try:
            if 'postgresql' in db_engine:
                with connection.cursor() as cursor:
                    # Get size in bytes
                    cursor.execute("SELECT pg_database_size(current_database());")
                    size_bytes = cursor.fetchone()[0]
                    size_mb = size_bytes / (1024 * 1024)
                    
                    cursor.execute("SELECT count(*) FROM pg_stat_activity;")
                    active_conns = cursor.fetchone()[0]
                
                metrics["File Size"] = f"{size_mb:.2f} MB"
                metrics["Active Connections"] = active_conns
                
                if size_mb > 1024 * 10: # 10 GB warning
                    status = "warning" if status != "critical" else "critical"
                    checks.append(CheckResult(name="Size", status="warning", message="DB size > 10GB"))
                
            else:
                # Fallback to SQLite
                if os.path.exists(db_name):
                    size_mb = os.path.getsize(db_name) / (1024 * 1024)
                    metrics["File Size"] = f"{size_mb:.2f} MB"
                    if size_mb > 1024:
                        status = "warning" if status != "critical" else "critical"
                        checks.append(CheckResult(name="Size", status="warning", message="DB size > 1GB"))
                else:
                    status = "critical"
                    checks.append(CheckResult(name="File Exists", status="critical", message="SQLite file not found"))
        except Exception as e:
            status = "warning"
            checks.append(CheckResult(name="Metrics", status="warning", message="Failed to fetch metrics"))

        return ProviderResult(
            status=status,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0),
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics
        )
