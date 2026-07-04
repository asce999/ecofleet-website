# Sprint 4 Report: Production Infrastructure (Phase 5)

## 1. Completed Work & Citations
- **Native Redis Cache**: Implemented Django native `RedisCache` as the primary cache backend, with a fallback to `FileBasedCache`.
  - Configured in `ecofleet/settings.py:147-163`
  - Removed race condition from `PerformanceMiddleware` by using atomic `cache.incr()` and storing metrics cleanly by endpoint. (`core/middleware.py:48-69`)
- **Celery Task Worker**: Created `process_ftl_import` task and set up `ecofleet/celery.py`.
  - Added Celery app instantiation in `ecofleet/celery.py:1-8` and exposed it in `ecofleet/__init__.py`.
  - Implemented the Celery task wrapper in `core/tasks.py`.
  - Switched FTL upload shadow importer to `process_ftl_import.delay()` when broker is present, retaining thread fallback (`core/views/ftl.py:382-390`).
- **RequestIDMiddleware & Audit Logging**: Introduced request traceability.
  - Implemented `RequestIDMiddleware` and `RequestIDFilter` using threading.local (`core/middleware.py:11-40`).
  - Added `X-Request-ID` to all responses (`core/middleware.py:38`).
  - Generated audit log records (`SystemEvent`) for login, login failure, and lockout in `core/signals.py:14-59`.
  - Added workbook activation event generation dynamically in `core/views/ftl.py`.
- **Workbook Lock Transition Documented**: 
  - Placed ponytail disclaimer indicating `workbook_lock` will be retired in Sprint 5 (`core/workbook/locking.py:25`).

## 2. Guard/Verification Evidence
- Unit test suite ran successfully: `Ran 36 tests in 13.503s OK`.
- Verification of new infrastructure components:
  - `RequestIDMiddlewareTest.test_request_id_header_presence` validated injection of `X-Request-ID` into response headers.
  - `SystemEventRequestIDTest.test_system_event_request_id_on_login` validated `SystemEvent` generation and population of `request_id` context.
- Verified absence of regression across existing DB migration and dual-read features.

## 3. Remaining Work & Blockers
- **Blockers**: None at present.
- **Remaining Work (Sprint 5)**: The final migration phase (Phase 6): making PostgreSQL the authoritative data source and deprecating Excel writes entirely.

## 4. Suggested Improvements
- Move from filesystem locks to a distributed locking mechanism (e.g., Redis-based locks) to ensure robust concurrency control once Celery workers run on isolated nodes.
- Improve error handling to retry failed background workbook imports in Celery via `autoretry_for`.
- Move CSP style requirements away from `'unsafe-inline'` once we extract dynamic template styling.

## 5. Technical Debt
- **Thread Fallback**: The `threading.Thread` shadow importer fallback is still in place; when the multi-node infrastructure is mandated, this code path should be purged to ensure horizontal scale without process boundaries.
- **Lost Excel Fields**: `etd` and `delivery_date` still lost on save; the DB schema will eventually be authoritative for them in Sprint 5.

## 6. Website Rating
- **7.5 / 10**: The transition from local file-based dependencies (FileBasedCache, threading, lockfiles) to scalable infrastructure components (Redis, Celery) improves horizontal scaling capabilities significantly. 

## 7. Roadmap Alignment
- Matches **Phase 5 — Production Infrastructure** of the Master Roadmap (`roadmap.md`). 
- Specifically aligns with tasks F-07 (Redis cache), F-10 (Celery broker), F-08 (request-id middleware), and F-13 (lock relocation staging).
