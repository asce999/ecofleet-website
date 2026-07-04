# ADR 002: PostgreSQL Adoption

**Date**: 2026-06-30
**Status**: Accepted

## Context
The application historically relied on SQLite as its primary relational database while heavily utilizing Excel sheets for authoritative domain storage. This dual-brain structure led to race conditions, locked database files under load, and significant complexity in handling relational data queries, such as aggregating shipment statuses. To prepare for robust data integrity and future celery integration, we must adopt a production-grade database.

## Decision
We will adopt **PostgreSQL** as the primary relational database, phasing out SQLite.

## Method
1. Export existing data from SQLite using Django's `dumpdata` (excluding content types and auth permissions).
2. Install `psycopg[binary]` and `dj-database-url` to handle PostgreSQL connections dynamically via `DATABASE_URL` environment variables.
3. Update `ecofleet/settings.py` to use `dj_database_url` with a fallback to SQLite.
4. Run `migrate` against the new PostgreSQL database to build the schema.
5. Import legacy data using `loaddata datadump.json` into PostgreSQL.
6. The `datadump.json` file is added to `.gitignore` and `.gitattributes` to prevent accidentally committing sensitive user password hashes and PII, and must be permanently deleted by the operator once the import is verified.

## Consequences (Gotchas)
- **Local Dev Setup**: Developers must now have PostgreSQL running locally to test the application or run tests. 
- **Backups**: `backup_database.py` has been updated to dynamically branch based on the database engine. If PostgreSQL is detected, it delegates to `pg_dump` via `subprocess`. The `pg_dump` binary must exist on the host path.

## Rollback Procedure
If PostgreSQL adoption causes unexpected regression:
1. Revert `ecofleet/settings.py` to explicitly use SQLite.
2. Remove the `DATABASE_URL` entry from `.env` (or override it back to sqlite3).
3. Keep the old `db.sqlite3` file untouched.
4. Revert `requirements.txt` to remove psycopg if necessary.
