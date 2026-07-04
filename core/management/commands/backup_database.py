import os
import time
import gzip
import sqlite3
import shutil
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import SystemEvent

class Command(BaseCommand):
    help = 'Safely backs up the database (PostgreSQL or SQLite) and manages retention'

    def handle(self, *args, **options):
        engine = settings.DATABASES['default']['ENGINE']
        is_postgres = engine.endswith('postgresql')
        
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = 'sql.gz' if is_postgres else 'sqlite3.gz'
        backup_file = os.path.join(backup_dir, f'ecofleet_{timestamp}.{ext}')
        
        start_time = time.time()
        try:
            if is_postgres:
                db_name = settings.DATABASES['default']['NAME']
                db_user = settings.DATABASES['default'].get('USER', 'postgres')
                db_host = settings.DATABASES['default'].get('HOST', 'localhost')
                db_port = settings.DATABASES['default'].get('PORT', '5432')
                db_pass = settings.DATABASES['default'].get('PASSWORD', '')
                
                env = os.environ.copy()
                if db_pass:
                    env['PGPASSWORD'] = db_pass
                
                # We use a temporary sql file then gzip it
                temp_sql = os.path.join(backup_dir, f'temp_{timestamp}.sql')
                
                pg_dump_cmd = 'pg_dump'
                if os.name == 'nt':
                    # Try to find pg_dump in common Windows Postgres paths
                    import glob
                    possible_paths = glob.glob(r'C:\Program Files\PostgreSQL\*\bin\pg_dump.exe')
                    if possible_paths:
                        # Sort to get the latest version
                        pg_dump_cmd = sorted(possible_paths, reverse=True)[0]
                
                cmd = [pg_dump_cmd, '-U', db_user, '-h', db_host, '-p', str(db_port), '-F', 'p', '-f', temp_sql, db_name]
                
                subprocess.run(cmd, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                
                with open(temp_sql, 'rb') as f_in:
                    with gzip.open(backup_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(temp_sql)
            else:
                db_path = settings.DATABASES['default']['NAME']
                if not os.path.exists(db_path):
                    self.stdout.write(self.style.ERROR(f"Database not found at {db_path}"))
                    return

                temp_backup = os.path.join(backup_dir, f'temp_{timestamp}.sqlite3')
                
                source = sqlite3.connect(db_path)
                dest = sqlite3.connect(temp_backup)
                try:
                    source.backup(dest)
                finally:
                    dest.close()
                    source.close()
                    
                time.sleep(0.2)
                
                with open(temp_backup, 'rb') as f_in:
                    with gzip.open(backup_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                os.remove(temp_backup)
                
            duration = time.time() - start_time
            size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            
            all_backups = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith('ecofleet_') and (f.endswith('.sqlite3.gz') or f.endswith('.sql.gz'))],
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
            
        except subprocess.CalledProcessError as e:
            msg = f"PostgreSQL pg_dump failed: {e.stderr.decode('utf-8', errors='ignore')}"
            self.stdout.write(self.style.ERROR(msg))
            SystemEvent.objects.create(
                severity=SystemEvent.SEVERITY_CRITICAL,
                component="Database",
                event_type="Backup",
                title="Automated Backup Failed",
                message=msg
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
