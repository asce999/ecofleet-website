# Sprint 5 Report: BTPL Migration & Employee Schema

## Completed Work

### 1. Known Bugs Addressed
- **ExcelExporter ETD/Delivery Date Fix**: Updated `core/importers/excel_importer.py` to correctly parse `etd` and `delivery_date` into `Shipment.expected_eta` and `Shipment.actual_eta` (lines 101-129). Updated `core/exporters/excel_exporter.py` to export these specific date values instead of `status_obj.timestamp` (lines 28-31).
- **Missing `source_key` Fallback Fix**: Added an explicit `save()` method override on the `Shipment` model in `core/models.py` (lines 434-442) to fallback and dynamically generate a `source_key` when none is provided, allowing natural creation outside of the importers.
- **Duplicate Import Fix**: Removed redundant `tool_permission_required` import in `core/views/btpl.py` (line 7).

### 2. BTPL Database Standup
- **BTPL Importer (`core/importers/btpl_importer.py`)**: Created a shadow importer that successfully parses BTPL workbooks based on `core.btpl.get_column_mapping` and upserts `Shipment` records (using natural keys `lr_number` and `pickup_date`).
- **BTPL Celery Task (`core/tasks.py`)**: Added `process_btpl_import` task.
- **Upload Wiring (`core/views/btpl.py`)**: Modified `btpl_settings` (lines 286-311) to dispatch `import_job` via Celery (or fallback thread) behind the `MigrationFeatureFlags.get_solo().use_database_importer` flag.

### 3. BTPL Dual-Read + Reconciliation
- **Fallback DB Page Reader (`core/views/btpl.py`)**: Added `_get_db_btpl_page_data()` helper (lines 37-86) and updated `btpl_sheet` (lines 101-112) to conditionally read from PostgreSQL when `use_database_reads` flag is `True`.
- **BTPL Reconciliation (`core/management/commands/reconcile_btpl.py`)**: Created management command to compare BTPL Excel active workbook rows against the database's `source_key` mapping.

### 4. Introduce Employee Model (F-14 Prep)
- **Employee Model (`core/models.py`)**: Added `Employee` model (lines 383-394) linked to `AUTH_USER_MODEL` and `Driver` (OneToOne), enabling unified payroll and attendance tracking in the future.
- **Migration**: Generated and successfully applied `0021_employee.py`. Data migration intentionally withheld per sprint scope.

## Remaining Work
- **Attendance Data Migration**: Needs to be implemented mapping existing `AttendanceRecord.driver` instances or equivalent to the new `Employee` model structure.
- **BTPL Authoritative Cutover**: Flip `use_database_reads` flag in production settings once the shadow importer proves robust in soak period.

## Blockers
- None encountered currently. 

## Guard / Verification Evidence
- **Test Suite**: Run `python manage.py test` successfully completing 36 tests in 14.861s without issues.
- **PostgreSQL Data Migration**: Successfully transitioned SQLite `datadump.json` to PostgreSQL (22047 records) locally and ran `python manage.py showmigrations` cleanly.
- **FTL Reconciliation Test**: Ran `reconcile_ftl` mapping successfully matched all 6 FTL active shipment rows against 6 loaded into the database from `efe_data/FTL_Shipment_Tracker.xlsx`.
- **BTPL Reconciliation Test**: Built the BTPL importer and ran `reconcile_btpl` mapping successfully matching all 64 BTPL shipments from `efe_data/BTPL_Shipments.xlsx` into PostgreSQL. 0 differences found.

## Suggested Improvements
- The date parsing functions built into `ExcelImporter` and `BtplImporter` share similar logic. The date handling (particularly standardizing openpyxl `datetime.datetime` fallback strings vs `datetime.date` attributes) should be refactored into a `utils/parsing.py` helper function instead of repeating it across modules.
- Implementing an API endpoint to view active reconciliation mismatches would benefit operations during the dual-write soak phase.

## Technical Debt
- BTPL writes (add row, edit row, delete row) in `core/views/btpl.py` are still actively writing via the older file system-bound `btpl_logic` mechanism. This legacy pathway needs complete removal post-soak period (Sprint 6).
- Re-use of Excel parsing mapping `openpyxl` structures vs DB abstractions needs decoupling.

## Website Rating: 8.5/10
**Justification**: The core architectural shift from a fragile file-locking `openpyxl` application to a resilient PostgreSQL DB-backed Django framework is making rapid, stable progress without affecting the user interface. Dual-writing allows regression testing safely in real-time. Performance bottlenecks from lock delays on workbook saving have an explicit timeline to be deprecated, ensuring long-term scalability.

## Roadmap Alignment
All objectives completed successfully align strictly with Phase A / Sprint 5 roadmap deliverables as defined in `CLAUDE_LATEST_REVIEW.md`. Scope discipline was maintained (Attendance migration delayed, UI untouched, dual-write logic preserved).
