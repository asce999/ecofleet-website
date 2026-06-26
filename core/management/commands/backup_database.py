import os
import time
import gzip
import sqlite3
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import SystemEvent

class Command(BaseCommand):
    help = 'Safely backs up the SQLite database and manages retention'

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f"Database not found at {db_path}"))
            return

        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'ecofleet_{timestamp}.sqlite3.gz')
        
        start_time = time.time()
        try:
            # Use sqlite3 backup API
            temp_backup = os.path.join(backup_dir, f'temp_{timestamp}.sqlite3')
            
            import contextlib
            with contextlib.closing(sqlite3.connect(db_path)) as source:
                with contextlib.closing(sqlite3.connect(temp_backup)) as dest:
                    source.backup(dest)
            
            # Compress
            with open(temp_backup, 'rb') as f_in:
                with gzip.open(backup_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Clean temp
            os.remove(temp_backup)
            
            duration = time.time() - start_time
            size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            
            # Retention: keep last 30 backups
            all_backups = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith('ecofleet_') and f.endswith('.sqlite3.gz')],
                reverse=True
            )
            deleted = 0
            if len(all_backups) > 30:
                for old_backup in all_backups[30:]:
                    os.remove(os.path.join(backup_dir, old_backup))
                    deleted += 1

            msg = f"Backup created successfully: {os.path.basename(backup_file)} ({size_mb:.2f} MB) in {duration:.2f}s. Deleted {deleted} old backups."
            self.stdout.write(self.style.SUCCESS(msg))
            
            SystemEvent.objects.create(
                severity=SystemEvent.SEVERITY_INFO,
                component="Database",
                event_type="Backup",
                title="Automated Backup Completed",
                message=msg,
                metadata={"duration_s": duration, "size_mb": size_mb, "filename": os.path.basename(backup_file)}
            )
            
        except Exception as e:
            msg = f"Backup failed: {str(e)}"
            self.stdout.write(self.style.ERROR(msg))
            SystemEvent.objects.create(
                severity=SystemEvent.SEVERITY_CRITICAL,
                component="Database",
                event_type="Backup",
                title="Automated Backup Failed",
                message=msg
            )
