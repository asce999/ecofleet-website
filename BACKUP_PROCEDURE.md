# EcoFleet Express - Backup Procedure

## Automated Backups
Automated backups are handled by the `core/operations/providers/backup.py` provider, which checks if database backups exist within the expected timeframe.

## Manual Backups
If you need to manually backup the SQLite database:

1. Connect to the server or virtual machine running the application.
2. Navigate to the project root directory: `cd C:\Users\ardcr\Desktop\EcoFleetExpress` (or the equivalent deployment path).
3. Copy the database file to a safe location or the `backups` directory:
   ```bash
   cp db.sqlite3 backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3
   ```

## Restore Procedure
1. Stop the application server (e.g., `systemctl stop ecofleet`).
2. Move the corrupted/current database to a safe location: `mv db.sqlite3 db.sqlite3.corrupted`.
3. Copy the backup file to the project root: `cp backups/db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3`.
4. Start the application server: `systemctl start ecofleet`.

## Retention Policy
- Daily backups are retained for 7 days.
- Weekly backups are retained for 4 weeks.
- Monthly backups are retained for 1 year.
