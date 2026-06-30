# Sprint Execution Plan — Sprints 1 to 6 (Revised)

This plan outlines the file-level tasks, tests, guards, and rollback strategies for Sprints 1 through 6, in strict accordance with `CLAUDE_LATEST_REVIEW.md` and `prompt.md`.

## Sprint 1 — Stop the bleeding (P0 correctness)

**Tasks:**
1. **[MODIFY] `requirements.txt`**
   - Pin `python-dateutil` explicitly.
2. **[MODIFY] `core/views/ftl.py` (F-01)**
   - Add `import datetime` at the top of the file to fix the `NameError` on the FTL "edit row" path.
3. **[NEW] `tests/unit/core/test_ftl_views.py` (F-01)**
   - Add `test_get_row_with_date_does_not_500` regression test asserting `get_row` returns 200 with ISO-formatted dates.
4. **[MODIFY] `core/models.py` (F-02)**
   - Add a stable natural key `source_key` (`CharField(max_length=200, blank=True, db_index=True)`) to the `Shipment` model.
   - Add a `UniqueConstraint` on `['shipment_type', 'source_key']` using `condition=~Q(source_key='')`.
5. **[NEW] Migration for `Shipment` (F-02)**
   - Verify `Shipment` tables are empty (0 rows) and run `python manage.py makemigrations core`.
6. **[MODIFY] `core/importers/excel_importer.py` (F-02, F-11)**
   - In `_process_ftl_row`, compute `source_key` (`f"{lr}|{booking_date.isoformat() if booking_date else ''}"`).
   - Use `Shipment.objects.update_or_create` instead of `create`. Rows with no usable key must be recorded as `failed` (`ImportErrorRecord`), not inserted with an empty key.
   - Remove bare `except:` and replace with `except (ValueError, TypeError, dateutil.parser.ParserError):`.
   - Add `# TODO(phase-3): wired when dual-read/export lands` to dead scaffolds.
7. **[MODIFY] `core/tests/test_importers.py` (F-02)**
   - Add a double-import test running the importer twice against the same file and asserting the row count is stable.
8. **Write Sprint Report**
   - Write `docs/reports/sprint-1-report.md` using the §5 template (completed / remaining / blockers / guard evidence / suggested improvements / tech debt / rating / roadmap alignment / rollback).

**Tools used:** `betterbugs` (log F-01 and F-02 as tracked issues; mark validated when regression tests pass), `multi_replace_file_content`, `run_command` (makemigrations, test).
**Guard:** F-01 regression test passes. Double-import test keeps row count stable. Tests pass.
**Rollback:** Revert git commits (no schema changes to populated tables).

---

## Sprint 2 — Shift to PostgreSQL (P1, F-03)

**Tasks:**
1. **[MODIFY] `requirements.txt`**
   - Add `psycopg[binary]==3.2.*` and `dj-database-url==2.*`.
2. **[MODIFY] `ecofleet/settings.py`**
   - Replace `DATABASES` with `dj_database_url.config(...)`. Apply SQLite `OPTIONS` only if the engine ends with `sqlite3`.
3. **Data Migration Execution**
   - On SQLite, run: `python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.permission -e admin.logentry -e sessions.session --indent 2 -o datadump.json`
   - Create the Postgres DB as **UTF-8**; point `DATABASE_URL` at it.
   - Run `python manage.py migrate` then `python manage.py loaddata datadump.json`.
   - Verify row counts table-by-table (21,758 pincodes, 15 users).
4. **[NEW] `docs/adr/ADR-002-postgresql-adoption.md`**
   - Record the SQLite→Postgres decision, method, gotchas, and rollback.
5. **[MODIFY] `core/management/commands/backup_database.py`**
   - Update to branch on engine, using `pg_dump` when on Postgres and existing SQLite logic otherwise.
6. **[MODIFY] `README.md` & `.env.example`**
   - Update setup and config instructions for `DATABASE_URL`.
7. **Write Sprint Report**
   - Write `docs/reports/sprint-2-report.md` using the §5 template.

**Tools used:** `context7` (pull Django 6 `dumpdata`/`loaddata` & migrations docs, `dj-database-url`/`psycopg` docs), `run_command`, `playwright` (screenshots of smoke test saved into report).
**Guard:** Row counts match. App boots on SQLite with no `DATABASE_URL`. Full test suite passes on PG. Backup drill succeeds. `python manage.py check --deploy` run and findings addressed.
**Rollback:** Keep `db.sqlite3` unmodified, unset `DATABASE_URL`.

---

## Sprint 3 — Make the DB trustworthy (P1, on Postgres, F-04)

**Tasks:**
1. **[NEW] `core/management/commands/reconcile_ftl.py` (F-04)**
   - Create a read-only command that parses the active FTL workbook and DB, reports diffs, and exits non-zero on mismatch.
2. **[MODIFY] `core/views/ftl.py` (F-04)**
   - Implement dual-read logic in the page-data / preview builder (e.g. `preview`, `next_row`, `totals_row`), ensuring the identical context shape/keys are returned. `get_active_ftl_workbook` only locates the file. Excel remains the fallback.
3. **[NEW] `tests/unit/core/test_reconciliation.py`**
   - Add a test asserting context parity between the sheet path and the DB path to ensure template rendering is identical.
4. **Write Sprint Report**
   - Write `docs/reports/sprint-3-report.md` using the §5 template.

**Tools used:** `multi_replace_file_content`, `run_command` (test), `playwright`.
**Guard:** Reconciliation script runs and shows zero-diff. Golden-file/context parity tests pass.
**Rollback:** Flip `use_database_reads` flag back to False.

---

## Sprint 4 — Remaining infrastructure (P2)

**Tasks:**
1. **[MODIFY] `requirements.txt` & `ecofleet/settings.py` (F-07, F-10)**
   - Add `redis`, `celery`. Update `CACHES` to use Redis. Configure Celery.
2. **[MODIFY] `core/middleware.py` (F-07, F-08)**
   - Fix `PerformanceMiddleware` lost-update race (store view name instead of raw `request.path`).
   - Create `RequestIDMiddleware` to generate UUIDs per request and populate `SystemEvent.request_id`.
3. **[MODIFY] `core/views/ftl.py` & `core/importers/excel_importer.py` (F-10)**
   - Convert `process_ftl_workbook` thread to a Celery task. Track `ImportJob` status and expose to UI.
4. **[MODIFY] `core/models.py` & `core/decorators.py` (F-08)**
   - Emit `SystemEvent` with `request_id` on login success/failure, axes lockout, permission change, and workbook activation.
5. **[MODIFY] `core/workbook/locking.py` (F-13)**
   - Relocate filesystem lock to a Redis-backed lock.
6. **Write Sprint Report**
   - Write `docs/reports/sprint-4-report.md` using the §5 template.

**Tools used:** `context7` (pull Redis cache and Celery docs), `multi_replace_file_content`.
**Guard:** Dashboard metrics are stable under load test, log/event correlation works, Celery processes jobs successfully, multi-worker write test for Redis lock passes. `python manage.py check --deploy` run and findings addressed.
**Rollback:** Revert cache/celery settings and middleware changes.

---

## Sprint 5 — Domain cutover (P1)

> ⚠️ **OWNER-GATED TASK:** Stop and request explicit owner approval before flipping any domain to DB-authoritative. The reconciliation soak window is an owner decision.

**Tasks:**
1. **[MODIFY] `core/views/ftl.py` (F-04)**
   - Make DB authoritative for FTL (ONLY after owner approval of soak window). Wire `ExcelExporter` into `ftl_download`.
2. **[MODIFY] `core/importers/excel_importer.py` & `core/views/btpl.py` (F-04)**
   - Build BTPL idempotent importer (using `source_key` and `update_or_create`). Enable dual-read for BTPL.
3. **[MODIFY] `core/models.py` & `core/views/attendance.py` (F-14)**
   - Introduce `Employee` model as the first step of Attendance migration. Point `AttendanceRecord` to `Employee` instead of `Driver`. Build Attendance idempotent importer and enable dual-read.
4. **Write Sprint Report**
   - Write `docs/reports/sprint-5-report.md` using the §5 template.

**Tools used:** `multi_replace_file_content`, `run_command`.
**Guard:** FTL, BTPL, and Attendance reconciliations show zero-diff.
**Rollback:** Feature flags (`use_database_reads`, etc.). Revert DB-authoritative commits.

---

## Sprint 6 — Simplification & hardening (P2)

**Tasks:**
1. **[NEW] `core/utils/workbook_engine.py` (F-05)**
   - Extract `WorkbookGrid`/`SheetTable` abstraction parameterized by `HEADER_MAP`.
2. **[MODIFY] `core/ftl.py`, `core/btpl.py`, `core/attendance.py`, `core/cof.py` (F-05)**
   - Remove duplicated machinery and use the new engine. Remove `evaluate_cell` if possible by writing computed values to DB.
3. **[MODIFY] `ecofleet/settings.py` & Templates (F-06)**
   - Add `CSP_INCLUDE_NONCE_IN`. Use `nonce="{{ request.csp_nonce }}"` in `<script>`/`<style>` blocks. Add SRI to Chart.js. Start with `Report-Only`.
4. **[MODIFY] `core/models.py` & `core/decorators.py` (F-09)**
   - Migrate from `can_use_*` booleans to Django Groups/Permissions. Create `Role` enum for `'Director'`. Write both the booleans and new groups for one release for reversibility.
5. **[NEW] `core/*/templates_default/*.xlsx` & [MODIFY] Fallbacks (F-12)**
   - Add tracked seed templates or generate via `WorkbookManager`. Point fallback logic away from `efe_data/`.
6. **Write Sprint Report**
   - Write `docs/reports/sprint-6-report.md` using the §5 template.

**Tools used:** `context7` (pull `django-csp` nonces doc), `multi_replace_file_content`.
**Guard:** Golden-file round-trip tests preserve behavior. No CSP violations in `Report-Only`. Permission tests pass. First-deploy-from-clean test succeeds.
**Rollback:** Keep old modules and CSP flags. Maintain `can_use_*` booleans.

---

## Finalisation

**Tasks:**
1. **Update Knowledge Graph**
   - After all code is implemented and all sprint docs/reports are written, run `graphify update .` to refresh `graphify-out/`.
2. **Verify Dependencies**
   - Confirm no new import cycles were introduced by examining the graphify output.

---

> **Note to Project Owner:** Please review the revised implementation plan above. If approved, I will proceed to execute Sprint 1.
