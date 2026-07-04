# Sprint 2 Report — Shift to PostgreSQL (P1, F-03)

## 1. Completed work
- Replaced the hardcoded SQLite configuration in `ecofleet/settings.py` with `dj-database-url` to support dynamic PostgreSQL configuration via `DATABASE_URL` `.env` variables, while retaining SQLite as a fallback.
- Added `psycopg[binary]==3.3.4` and `dj-database-url==3.1.2` to `requirements.txt`.
- Generated `datadump.json` safely from SQLite using `dumpdata` (excluding ContentTypes, Permissions, Sessions, and LogEntries).
- Updated `.gitignore` and `.gitattributes` to explicitly ignore `datadump.json` to prevent accidentally committing auth credentials or PII.
- Rewrote `core/management/commands/backup_database.py` to correctly branch based on the active engine. If PostgreSQL is active, it now pipes a `pg_dump` backup directly into `gzip`.
- Updated `README.md` and `.env.example` with PostgreSQL setup instructions.
- Recorded `docs/adr/ADR-002-postgresql-adoption.md` detailing the Postgres adoption strategy.

## 2. Remaining work (Pending Owner Action)
Since PostgreSQL is not installed natively in the execution environment, the following steps must be completed locally by the owner:
1. Ensure your local PostgreSQL service is running.
2. Run `createdb -U postgres ecofleet --encoding=UTF8`.
3. Run `python manage.py migrate` to apply all schemas.
4. Run `python manage.py loaddata datadump.json` to load the data.
5. Verify row counts and data integrity.
6. **Critically:** Delete the `datadump.json` file.

## 3. Blockers
None.

## 4. Guard / verification evidence
- `datadump.json` was generated successfully and is present locally.
- `requirements.txt` has successfully resolved and installed the Postgres drivers during execution.
- `.gitignore` explicitly prevents `datadump.json` from being tracked or exported.
- The PostgreSQL `DATABASE_URL` structure is correctly set up in `.env.example`.

## 5. Suggested improvements
Once data is securely migrated to PostgreSQL and tested in production, we can completely remove the SQLite fallback from the codebase and fully drop SQLite integration.

## 6. Technical debt
There's currently no automated CI test running against a real PostgreSQL instance; test environments should be upgraded to use PostgreSQL via Docker/actions to prevent SQLite/Postgres dialect drift.

## 7. Website rating (/10) with detailed justification
**6/10**. Moving off SQLite natively solves concurrency and database locking issues. However, the UI still relies completely on scraping Excel sheets rather than using the database as the primary source of truth.

## 8. Roadmap alignment
Aligns directly with Phase 3, Sprint 2 (Shift to PostgreSQL). Addresses flaw ID F-03 from `CLAUDE_LATEST_REVIEW.md`.

## 9. Rollback procedure for this sprint
- Revert `ecofleet/settings.py` to the previous SQLite hardcode.
- Remove `psycopg` and `dj-database-url` from `requirements.txt`.
- Ignore or remove the Postgres variables from `.env`.
