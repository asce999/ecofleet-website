# Phase 5 — Storage & Database Security Audit

## 1. Executive Summary
This report summarizes Phase 5 of the EcoFleet AI Audit Framework, focusing on the storage architecture, SQLite implementation, FileField persistence, and disaster recovery readiness. The assessment reveals critical deficiencies in the disaster recovery strategy and database restoration logic, as well as medium-severity issues regarding storage scalability and atomicity.

## 2. Storage Architecture
The application relies on local storage via Django's default `FileSystemStorage` (`MEDIA_ROOT = BASE_DIR / 'media'`). Storage is highly stateful, holding the authoritative `CofWorkbook`, `BtplWorkbook`, `AttendanceWorkbook`, and `FtlWorkbook` files alongside `ToolRunFile` output archives. 

## 3. Database Architecture
The application uses SQLite3 in Write-Ahead Logging (WAL) mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`), with a configured timeout of 20 seconds. This is an appropriate architectural choice for concurrent read-heavy, light-write workloads, avoiding traditional SQLite locking bottlenecks.

## 4. Workbook Lifecycle
1. **Upload**: Administrator uploads `.xlsx`.
2. **Storage**: Django saves it in `media/`. A database record tracks the path and sets `is_active=True`.
3. **Modification**: Forms/API views directly mutate the physical file via `openpyxl.save()`.
4. **Archival**: Replacing a sheet sets `is_active=False` on the old DB record and uploads a new file.
5. **Deletion**: The application relies purely on soft-deletes (`is_active=False`). Physical files are never deleted.

## 5. Trust Boundaries
- **Database Boundary**: Standard ORM protection is in place.
- **Filesystem Boundary**: Users can upload files that are persisted in the local filesystem; the application trusts the file extension and MIME type validation evaluated in Phase 4.

## 6. Data Integrity Review
Data integrity is heavily dependent on the filesystem. Since the core business records (Attendance, FTL, BTPL, COF) are Excel files, the database acts primarily as an index. Modifying an Excel file via `openpyxl` operates independently of SQLite transactions, meaning database rollbacks cannot undo filesystem changes.

## 7. Scalability Assessment
- **Database**: SQLite with WAL is highly scalable for this application's current concurrency model.
- **Storage**: Storage scalability is flawed. Continuous generation of `ToolRunFile` reports and uploading of new workbooks without a cleanup job will linearly consume disk space until exhaustion.

## 8. Storage Strengths
- **WAL Mode**: SQLite is configured efficiently to prevent "database is locked" errors.
- **Automated DB Backups**: The `backup_database.py` script correctly uses the safe `sqlite3.backup()` API and manages retention automatically.

---

## 9. Confirmed Findings

### Missing Media Backup Destroys System of Record
- **Severity:** Critical
- **Confidence:** Confirmed
- **Business Asset:** Database / Uploaded Workbooks / Business Continuity
- **Likelihood:** High
- **Impact:** Critical
- **Verification Method:** Code Review
- **Evidence Quality:** Strong

**Evidence:**
In `core/management/commands/backup_database.py`:
```python
        db_path = settings.DATABASES['default']['NAME']
        ...
        source = sqlite3.connect(db_path)
        dest = sqlite3.connect(temp_backup)
        source.backup(dest)
```

**Why this is a Vulnerability:**
The backup script perfectly captures the SQLite database, but completely ignores the `media/` directory. In EcoFleet, the SQLite database only stores file paths (via `FileField`). The actual business data (FTL trackers, BTPL records, Attendance sheets) lives in the Excel files inside `media/`. If a server crashes or disk fails, restoring the DB backup will result in broken file references, and all business data will be irrecoverably lost.

**Counter Argument (Pass 2 Challenge):**
*Maybe backups are handled at the VM/OS level?* 
If OS-level snapshots are used, this custom backup script is redundant. However, as an application-provided feature intended to "Safely back up the SQLite database and manage retention", it presents a false sense of security to the administrators relying on it.

**Attack Preconditions:**
- A catastrophic event (ransomware, server crash, accidental deletion) requires a full restore.

**Exploitation Scenario:**
1. A server failure corrupts the disk.
2. The sysadmin pulls the latest `ecofleet_20260627_120000.sqlite3.gz` from the backups folder.
3. They restore the database.
4. Users log in, click "Download Active BTPL Sheet", and receive a 404/500 error because the physical file is gone. The business data is lost.

**Existing Mitigations:**
- None for the `media/` folder.

**Recommended Fix:**
Modify the backup script to create a `.tar.gz` archive containing *both* the SQLite database snapshot and the entire `media/` directory.

**Remediation Difficulty:** Easy
**Estimated Development Effort:** 2 hours
**Regression Risk:** Low (Script runs asynchronously)
**Suggested Testing Strategy:** Execute the backup script, extract the resulting archive, and verify both `db.sqlite3` and the `media/` directory are present.

**Mapping:**
- OWASP: A05:2021 – Security Misconfiguration
- CWE: CWE-930 (Omission of Backup)


### Live Database Restore Causes Irreversible Corruption (WAL Conflict)
- **Severity:** Critical
- **Confidence:** Confirmed
- **Business Asset:** Database Data Integrity
- **Likelihood:** Medium
- **Impact:** Critical
- **Verification Method:** Architecture Review
- **Evidence Quality:** Strong

**Evidence:**
In `ecofleet/settings.py`:
```python
'init_command': 'PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;',
```
In `core/management/commands/restore_database.py`:
```python
if backup_path.endswith('.gz'):
    with gzip.open(backup_path, 'rb') as f_in:
        with open(db_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
```

**Why this is a Vulnerability:**
SQLite in WAL (Write-Ahead Logging) mode utilizes three files: `db.sqlite3`, `db.sqlite3-wal`, and `db.sqlite3-shm`. The `restore_database.py` script naively overwrites only the main `db.sqlite3` file using standard file I/O (`shutil.copyfileobj`) while the Django application might be running. If the application is alive, the old `.sqlite3-wal` file remains on disk and contains uncheckpointed transactions from the *previous* corrupted state. When SQLite next accesses the database, it will apply the old WAL file to the newly restored main database file, fundamentally corrupting it.

**Counter Argument (Pass 2 Challenge):**
*If the admin stops the webserver before running the restore command, isn't it safe?*
Yes, but the script does not enforce this, check for it, or warn the user about it. Even if stopped, the `.sqlite3-wal` file might still exist on disk if it wasn't gracefully checkpointed, meaning it must be manually deleted before restoring the main `.sqlite3` file.

**Attack Preconditions:**
- An administrator executes the `restore_database` management command.

**Exploitation Scenario:**
1. Admin runs `python manage.py restore_database backup.gz`.
2. The script overwrites `db.sqlite3`.
3. The old `db.sqlite3-wal` file remains on disk.
4. The web server issues a query. SQLite sees the WAL file and merges its contents into the restored database, creating corrupted, mixed-state records.

**Existing Mitigations:**
- The script creates a `.safety_copy_before_restore`, but if the DB is corrupted by the WAL merge, manual intervention is required to recover.

**Recommended Fix:**
In `restore_database.py`, explicitly delete the `db.sqlite3-wal` and `db.sqlite3-shm` files if they exist before or immediately after replacing the main `db.sqlite3` file, and forcefully print a warning that the webserver (Gunicorn/Uvicorn) MUST be stopped before running the command.

**Remediation Difficulty:** Easy
**Estimated Development Effort:** 30 minutes
**Regression Risk:** Medium
**Suggested Testing Strategy:** Start the web server, write data to force a WAL file creation, run the restore script, and verify the DB is not corrupted.

**Mapping:**
- OWASP: A05:2021 – Security Misconfiguration
- CWE: CWE-564 (SQL Injection: Hibernate) - *Not SQLi, but CWE-362 (Race Condition) / Data Corruption*


### Unbounded Storage Exhaustion via Orphaned Media Files
- **Severity:** Medium
- **Confidence:** Confirmed
- **Business Asset:** Storage Availability
- **Likelihood:** High
- **Impact:** Medium
- **Verification Method:** Code Review
- **Evidence Quality:** Strong

**Evidence:**
In `core/views/btpl.py` (and others):
```python
BtplWorkbook.objects.filter(is_active=True).update(is_active=False)
```
In `core/models.py`, `ToolRunFile` uses standard `models.FileField`. 

**Why this is a Vulnerability:**
Django's `FileField` does not automatically delete physical files from disk when the database record is deleted (since Django 1.3), nor does it delete files when they are replaced or soft-deleted (`is_active=False`). Every time a user uploads a new tracker or generates a report, a new file is written to the `media/` directory. There is no cleanup cron job, Celery task, or management command to prune these files, guaranteeing eventual disk exhaustion.

**Counter Argument (Pass 2 Challenge):**
*Storage is cheap, is this really a security issue?*
It becomes a security issue (Denial of Service) when the disk hits 100% capacity, instantly causing the database (SQLite) to fail writes and crashing the entire application.

**Attack Preconditions:**
- Standard operational usage over an extended period.

**Exploitation Scenario:**
1. Operations team uses the portal daily, generating 50 reports and uploading 10 workbooks a day.
2. After 6 months, the `media/` folder reaches 20GB.
3. The server's 20GB volume fills up.
4. SQLite throws `database or disk is full` exceptions, causing a total application outage.

**Existing Mitigations:**
- None.

**Recommended Fix:**
Implement a `cleanup_media.py` management command (to be run via cron) that identifies and deletes files older than a specific retention period (e.g., 90 days), or use Django signals (`post_delete`) to remove physical files when records are deleted (though soft-deletes require a custom cleanup approach).

**Remediation Difficulty:** Medium
**Estimated Development Effort:** 2 hours
**Regression Risk:** Medium
**Suggested Testing Strategy:** Run the new cleanup script and assert that orphaned files older than the retention threshold are removed from disk, while active files remain untouched.


### Missing Atomic Transactions on Batch Data Updates
- **Severity:** Medium
- **Confidence:** Confirmed
- **Business Asset:** Payroll / Database Integrity
- **Likelihood:** Medium
- **Impact:** Medium
- **Verification Method:** Code Review
- **Evidence Quality:** Strong

**Evidence:**
In `core/views/attendance.py` (`salary_calculator`):
```python
for emp in data['employees']:
    # Data extraction...
    if any(v is not None for v in [inc_val, allow_val, adv_val, lwf_val, oth_val, csh_val]):
        EmployeeSalaryOverride.objects.update_or_create(
            employee_name=emp_name,
            defaults={...}
        )
```

**Why this is a Vulnerability:**
The loop iterates through potentially hundreds of employees, committing database writes for each one. The view does not use `transaction.atomic()`. If an exception occurs (e.g., database constraint failure, network hiccup) on the 50th employee, the view crashes and returns a 500 error. The first 49 employees will have updated salaries, while the rest will not. This leaves the system in an inconsistent state, causing payroll discrepancies.

**Counter Argument (Pass 2 Challenge):**
*The user can just fix the input and submit again?*
Yes, but they won't know which records were updated and which weren't, leading to confusion and potential double-deductions if they aren't careful.

**Attack Preconditions:**
- An administrator submits a bulk update containing at least one invalid field that bypasses frontend validation but triggers a backend or DB error.

**Exploitation Scenario:**
1. Admin submits salary overrides for 100 employees.
2. Employee 50 has a maliciously or accidentally crafted invalid decimal value.
3. The server processes 1 through 49, saving them.
4. Employee 50 throws a `ValueError`, crashing the view.
5. Payroll is now out of sync, with half the workforce receiving different rules than the other half.

**Existing Mitigations:**
- A custom `parse_dec()` wrapper attempts to handle empty strings, but it doesn't prevent all failures, nor does it provide transaction rollback.

**Recommended Fix:**
Wrap the `for emp in data['employees']:` block in a `with transaction.atomic():` context manager.

**Remediation Difficulty:** Easy
**Estimated Development Effort:** 30 minutes
**Regression Risk:** Low
**Suggested Testing Strategy:** Intentionally trigger an exception halfway through the loop and assert that no records were modified in the database.

---

## 10. Likely Findings
- **Data Desync between Filesystem and Database**: Because modifying an Excel sheet and writing a `ToolRun` audit log are not atomic across boundaries (Filesystem + SQLite), a crash between `wb.save()` and `ToolRun.objects.create()` will result in the Excel sheet being updated without any audit trail in the database. 

## 11. Potential Findings
- **SQLite Write Contention**: Under heavy concurrent load, multiple users uploading reports simultaneously might experience SQLite `database is locked` timeouts, despite WAL mode and the 20s timeout, because Django's ORM holds connections open during long request-response cycles.

## 12. Attack Chains
- **Denial of Service Chain**: Attacker uses a script to repeatedly upload 9MB tracking workbooks (bypassing the 10MB limit). Because previous files are never deleted (Unbounded Storage Exhaustion), the attacker fills the entire disk volume in minutes, causing a complete system outage.

---

## 13. Engineering Backlog

| ID | Issue | Priority | Estimated Effort | Regression Risk | Suggested Owner |
|----|-------|----------|------------------|-----------------|-----------------|
| STG-01 | Backup script misses `media/` folder | Critical | 2 hours | Low | DevOps |
| STG-02 | Restore script corrupts WAL database | Critical | 30 mins | Medium | Database |
| STG-03 | Missing cron cleanup for orphaned files | High | 2 hours | Medium | Backend |
| STG-04 | Add `transaction.atomic` to batch views | Medium | 30 mins | Low | Backend |
| STG-05 | Implement OS-level locking for all workbooks | Medium | 1 day | High | Architecture |

---

## 14. Hardening Recommendations
1. **Unify Backups**: Redesign the backup command to generate a tarball containing both the SQLite database snapshot and the entire `media/` directory.
2. **Safe Restoration**: The restore script must enforce a web server shutdown and aggressively clear `.sqlite3-wal` and `.sqlite3-shm` files.
3. **Automated Cleanup**: Write a Django management command to permanently delete `ToolRunFile`s and archived Workbooks older than 30 days, and run it via cron.
4. **Transaction Boundaries**: Apply `transaction.atomic()` to any view that modifies multiple database rows.

---

## 15. Storage Security Score (0–10)
**3 / 10**
The database configuration is reasonably scalable (WAL mode), but the disaster recovery mechanisms are fundamentally broken and pose an immediate risk of irreversible data loss.

## 16. Overall Risk Rating
**CRITICAL**

## 17. Storage Maturity Assessment
The storage architecture reflects an early-stage MVP. The reliance on local disk for authoritative business logic without a unified DB+Filesystem backup strategy renders the application extremely fragile to hardware failure or operator error. Maturity is currently **Low**.
