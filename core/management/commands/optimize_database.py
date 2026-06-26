import time
import sqlite3
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import SystemEvent

class Command(BaseCommand):
    help = 'Safely runs VACUUM and ANALYZE on the SQLite database to reclaim space and optimize query plans.'

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f"Database not found at {db_path}"))
            return

        original_size = os.path.getsize(db_path)
        start_time = time.time()
        
        try:
            with sqlite3.connect(db_path) as conn:
                self.stdout.write("Running VACUUM...")
                conn.execute("VACUUM")
                
                self.stdout.write("Running ANALYZE...")
                conn.execute("ANALYZE")
                
            duration = time.time() - start_time
            new_size = os.path.getsize(db_path)
            freed_space = original_size - new_size
            
            msg = f"Database optimized in {duration:.2f}s. Freed {freed_space / 1024:.2f} KB."
            self.stdout.write(self.style.SUCCESS(msg))
            
            SystemEvent.objects.create(
                severity=SystemEvent.SEVERITY_INFO,
                component="Database",
                event_type="Optimize",
                title="Database Optimized",
                message=msg,
                metadata={"duration_s": duration, "freed_bytes": freed_space, "new_size_bytes": new_size}
            )
            
        except Exception as e:
            msg = f"Database optimization failed: {str(e)}"
            self.stdout.write(self.style.ERROR(msg))
            SystemEvent.objects.create(
                severity=SystemEvent.SEVERITY_WARNING,
                component="Database",
                event_type="Optimize",
                title="Database Optimization Failed",
                message=msg
            )
