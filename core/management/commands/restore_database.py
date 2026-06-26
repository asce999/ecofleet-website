import os
import gzip
import shutil
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.models import SystemEvent

class Command(BaseCommand):
    help = 'Restores the SQLite database from a backup. Requires explicit confirmation.'

    def add_arguments(self, parser):
        parser.add_argument('backup_filename', type=str, help='The name of the backup file in the backups/ directory to restore from')
        parser.add_argument('--force', action='store_true', help='Force restore without confirmation prompt')

    def handle(self, *args, **options):
        filename = options['backup_filename']
        backup_path = os.path.join(settings.BASE_DIR, 'backups', filename)
        
        if not os.path.exists(backup_path):
            raise CommandError(f"Backup file '{backup_path}' does not exist.")
            
        db_path = settings.DATABASES['default']['NAME']
        
        if not options['force']:
            self.stdout.write(self.style.WARNING(f"WARNING: This will overwrite your current database ({db_path}) with the backup ({backup_path})."))
            self.stdout.write(self.style.WARNING("All data created since the backup will be permanently lost."))
            confirm = input("Are you sure you want to proceed? Type 'RESTORE' to confirm: ")
            if confirm != 'RESTORE':
                self.stdout.write(self.style.ERROR("Restore cancelled."))
                return

        try:
            # Create a safety copy of current db before overwrite just in case
            if os.path.exists(db_path):
                safety_copy = f"{db_path}.safety_copy_before_restore"
                shutil.copy2(db_path, safety_copy)
                
            if backup_path.endswith('.gz'):
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(db_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, db_path)

            msg = f"Database successfully restored from {filename}"
            self.stdout.write(self.style.SUCCESS(msg))
            
            SystemEvent.objects.create(
                severity=SystemEvent.SEVERITY_WARNING,
                component="Database",
                event_type="Restore",
                title="Database Restored",
                message=msg,
                metadata={"filename": filename}
            )
            
        except Exception as e:
            msg = f"Database restore failed: {str(e)}"
            self.stdout.write(self.style.ERROR(msg))
            SystemEvent.objects.create(
                severity=SystemEvent.SEVERITY_CRITICAL,
                component="Database",
                event_type="Restore",
                title="Database Restore Failed",
                message=msg
            )
