# Sprint 1 Report — Stop the bleeding (P0 correctness)

## 1. Completed work
- Pinned `python-dateutil==2.9.0.post0` in `requirements.txt`.
- Fixed `NameError` in `core/views/ftl.py` by adding `import datetime` (F-01).
- Added regression test `test_get_row_with_date_does_not_500` to `tests/unit/core/test_ftl_views.py`.
- Added `source_key` to the `Shipment` model (a stable natural key for idempotency) and a `UniqueConstraint` on `['shipment_type', 'source_key']` with the `~Q(source_key='')` condition. Generated and applied the schema migration (F-02).
- Updated `ExcelImporter` in `core/importers/excel_importer.py` to:
  - Compute `source_key` as `f"{lr}|{booking_date.isoformat()}"`.
  - Use `Shipment.objects.update_or_create`.
  - Raise `ValueError` for rows with no usable key (recorded as `ImportErrorRecord`).
  - Replace the bare `except:` clause with `except (ValueError, TypeError, dateutil.parser.ParserError):` (F-11).
- Added Phase-3 `TODO` annotations to dead scaffolds `ExcelExporter` and `use_database_reads`.
- Added a double-import regression test in `tests/unit/core/test_importers.py` to verify idempotency.

*(Note: Issue tracking via BetterBugs MCP was attempted but skipped/aborted due to MCP timeout).*

## 2. Remaining work
None for Sprint 1. The codebase is now stable enough to begin the PostgreSQL migration.

## 3. Blockers
None. 

## 4. Guard / verification evidence
- **F-01 Regression Test**: Passed. The `get_row` API now correctly formats dates without 500 errors.
- **F-02 Idempotency Test**: Passed. Double-importing the same sheet results in stable row counts (0 failed rows, 2 shipments total).
- **Test Suite Output**:
  ```text
  Ran 30 tests in 11.215s
  OK
  System check identified no issues (0 silenced).
  ```

## 5. Suggested improvements
Dual-read logic in upcoming sprints should ensure `dateutil` parsing is robust across both Excel and DB data representations. We should also monitor the importer's execution time for very large sheets, as row-by-row `update_or_create` can be I/O heavy.

## 6. Technical debt
The shadow importer currently runs sequentially on a single thread. In Sprint 4, this will be offloaded to Celery to prevent blocking the UI request.

## 7. Website rating (/10) with detailed justification
**5/10**. The critical correctness bugs (500s on row edits) are fixed, but the application is still vulnerable to data loss as it's running on SQLite with a filesystem-based Excel source of truth. 

## 8. Roadmap alignment
Aligns directly with Phase 3, Sprint 1 (P0 correctness). Addresses flaw IDs F-01, F-02, and F-11 from `CLAUDE_LATEST_REVIEW.md`.

## 9. Rollback procedure for this sprint
- Un-apply the migration on SQLite: `python manage.py migrate core 0019`.
- Revert the git commits for `core/views/ftl.py`, `core/importers/excel_importer.py`, `core/models.py`, `requirements.txt`, and the new test files.
