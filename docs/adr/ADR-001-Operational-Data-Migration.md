# Architecture Decision Record: ADR-001
## Operational Data Migration

**Status:** Proposed / Under Review  
**Date:** 2026-06-30  
**Phase:** 2  

---

## 1. Current State Analysis

### 1.1 Existing Architecture
EcoFleet Express currently relies on an Excel-centric operational paradigm. The system manages core logistics and HR data by storing and manipulating `.xlsx` files (`AttendanceWorkbook`, `BtplWorkbook`, `FtlWorkbook`, `CofWorkbook`) directly on the filesystem (`media/`). A Singleton pattern in the Django database points to the currently `is_active=True` workbook, which acts as the source of truth for the portal.

### 1.2 Identified Weaknesses & Technical Debt
- **Concurrency & Locking Bottlenecks:** To prevent data corruption, operations require filesystem-level locking (PID/TTL locks). This serializes reads and writes, making horizontal scaling impossible and limiting performance under multi-user load.
- **Performance Overhead:** The `openpyxl` library parses the entire workbook into memory for any modification. An $O(1)$ database update is currently an $O(N)$ file manipulation.
- **Data Integrity Constraints:** The application blindly trusts the schema and cell formatting of user-uploaded Excel files. Typographical errors, column shifts, and data type violations frequently break parsing logic.
- **Lack of Relational Modeling:** Entities like `Driver`, `Vehicle`, and `Customer` exist only as loosely typed strings within spreadsheet rows. Querying a driver's historical performance across different shipment types requires scanning massive disconnected files.
- **Provider Architecture Tension:** The Operations Center monitors health by polling file presence and rudimentary parsing, which is brittle and slow compared to a SQL `COUNT(*)` operation.

*Conclusion:* Excel must be retired as an operational database. It cannot scale indefinitely and presents a severe reliability ceiling.

---

## 2. Business Requirements

The migration strategy must satisfy the following organizational goals:
- **Scalability Goals:** Support concurrent read/write operations by 100+ active logistics operators without file contention.
- **Reliability Goals:** Guarantee ACID compliance for all operational transactions, ensuring zero data loss during concurrent uploads.
- **Reporting & Analytics Goals:** Enable real-time operational dashboarding, historical trend analysis, and complex queries (e.g., cross-referencing driver attendance with FTL shipment delays).
- **Fleet & Shipment Goals:** Establish normalized master data for Vehicles and Drivers to track maintenance, capacity, and performance.
- **Zero Disruption:** The portal must remain fully operational for employees during the migration rollout.

---

## 3. Database Strategy

The future architecture dictates **PostgreSQL** as the sole source of truth for operational data.

- **Separation of Concerns:** Django ORM handles business logic, PostgreSQL enforces data constraints, and Excel acts purely as a transport format (Import/Export).
- **Normalization Strategy:** Core entities (Customers, Drivers, Vehicles) will be normalized to 3NF. Transactional entities (Shipments, Consignments) will maintain foreign keys to master data.
- **JSONB for Flexibility:** Highly variable auxiliary metadata (e.g., custom COF fields, unstructured shipment notes) will be stored in PostgreSQL `JSONB` columns to avoid schema bloat.
- **Referential Integrity & Constraints:** PostgreSQL `FOREIGN KEY`, `CHECK`, and `UNIQUE` constraints will enforce data quality at the database level—a massive upgrade from Excel cell validation.
- **Transactions:** High-volume imports will be wrapped in `transaction.atomic()` to ensure batch operations succeed or fail entirely.

*Note on Timeline:* PostgreSQL is the target operational database defined by ADR-001 in Phase 2. Phase 3 introduces the Shipment Domain built strictly around this target architecture. Phase 5 focuses on production infrastructure, operational readiness, and supporting services (e.g., Redis, background processing), but the PostgreSQL schemas themselves will be introduced and utilized starting in Phase 3.

---

## 4. Domain Model Design

The following bounded contexts and entities will be introduced in Phase 3:

### 4.1 Shipment Domain
- **Shipment:** The root entity. Tracks overarching metrics (Origin, Destination, Expected ETA, Actual ETA). Includes an enum `shipment_type` (`FTL`, `BTPL`).
- **ShipmentStatus:** Enum representing state (`DRAFT`, `DISPATCHED`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`).
- **TrackingHistory:** Append-only ledger recording timestamps, locations, and status changes for auditability.
- **Consignment:** Child entity of `Shipment` (crucial for BTPL), representing individual pallets/packages, their weight, and specific receivers.

### 4.2 Fleet Domain (Master Data)
- **Vehicle:** Tracks Registration Number, Capacity, Vehicle Type, and Status.
- **Driver:** Tracks Name, License Information, UAN/ESIC (bridging to Attendance), and Status.

### 4.3 Human Resources Domain
- **AttendanceRecord:** Replaces the monolithic Attendance Workbook. Tracks `Employee` and `Date` with daily statuses (`Present`, `Absent`, `Leave`, `Half-Day`), allowing fast querying of payroll limits.

*Why these exist:* They replace the strings embedded in `.xlsx` rows with strictly typed relationships, enabling cross-domain insights.

---

## 5. Excel Strategy

Under the new architecture, Excel's role fundamentally changes:
- **What remains in Excel:** Nothing operational.
- **What moves to PostgreSQL:** All transactional state, historical data, and master records.
- **What becomes Import:** Bulk data entry templates (e.g., a manager uploading a 500-row BTPL manifest).
- **What becomes Export:** Compliance reports, end-of-month payroll archives, and vendor-facing shipment confirmations.
- **What becomes Archival:** Raw uploaded workbooks will be saved directly to `media/archived_uploads/` (or AWS S3) for audit purposes only. They are never queried for business logic.

---

## 6. Migration Strategy

We will utilize a variation of the **Strangler Fig Pattern** supported by a robust **Feature Flag Strategy** to ensure a seamless transition and controlled rollout.

### Feature Flags
The rollout will be governed by environment variables or database-backed feature flags (e.g., Django Waffle):
- `USE_DATABASE_IMPORTER`: Enables Shadow Mode, parsing uploaded Excel files into PostgreSQL asynchronously.
- `USE_DATABASE_READS`: Enables Dual-Read Validation and switches UI dashboards to query PostgreSQL instead of Excel.
- `USE_DATABASE_EXPORTS`: Replaces static Excel downloads with dynamically generated workbooks from the database.

### Rollout Stages
- **Migration Stage 1 (Foundation):** Deploy the PostgreSQL schemas. Keep the portal pointing to the legacy Excel logic.
- **Migration Stage 2 (Shadow Import):** Enable `USE_DATABASE_IMPORTER`. When a user uploads an Excel file, it is processed synchronously by the legacy system, and asynchronously parsed and inserted into PostgreSQL.
- **Migration Stage 3 (Dual Read/Write Verification):** Enable `USE_DATABASE_READS`. Modify the `ShipmentService` interfaces to read from PostgreSQL, but continue writing to Excel as a fallback. Verify data parity via nightly reconciliation scripts.
- **Production Cutover:** Legacy `workbook.save()` is disabled. Enable `USE_DATABASE_EXPORTS`. The portal reads and writes exclusively to PostgreSQL. Excel uploads become purely "Imports," and Excel downloads become purely "Exports."

---

## 7. Import Architecture

The Importer is the bridge between human-generated Excel files and the strict PostgreSQL database.
- **Validation:** Importers utilize `pydantic` or Django Forms to validate row-level data types *before* hitting the database.
- **Duplicate Detection:** Composite natural keys (e.g., `lorry_number` + `dispatch_date`) combined with PostgreSQL `UNIQUE` constraints will reject duplicate row imports.
- **Error Handling & Logging:** A row-level failure will not fail the entire batch. Successful rows are committed, while failed rows are emitted as `ImportErrorRecord` entities, allowing the user to download an "Error Report Excel," fix the issues, and re-upload.

### ImportJob Lifecycle
To manage the asynchronous nature of large Excel parsing, the system will rely on an `ImportJob` entity tracking the ingestion process.

**States:**
- `PENDING`: Job is queued but not yet picked up by the background worker.
- `RUNNING`: The worker is actively parsing and inserting rows.
- `COMPLETED`: All rows successfully inserted.
- `FAILED`: Fatal error (e.g., file corruption, out of memory).
- `PARTIAL_SUCCESS`: Batch finished, but some rows were rejected and logged as `ImportErrorRecord`.

**Operational Policies:**
- **Progress Tracking:** The `ImportJob` updates a `rows_processed` and `total_rows` counter for real-time frontend WebSocket/Polling updates.
- **Retry Policy:** `FAILED` jobs due to transient database locks or network timeouts will be retried automatically (up to 3 times) with exponential backoff. Data-validation errors (`PARTIAL_SUCCESS`) will not be retried automatically; they require human correction.
- **Retention Policy:** `ImportJob` records and associated raw Excel blobs will be retained in fast storage for 30 days, then moved to cold storage (AWS S3 Glacier).
- **Audit Logging:** Every state transition and user initiating the upload is logged to satisfy compliance constraints.

---

## 8. Export Architecture

- **Exporter Role:** Translates PostgreSQL querysets into formatted `.xlsx` streams using `openpyxl` or `pandas`.
- **Performance:** For massive exports, Django's `StreamingHttpResponse` combined with generator expressions will stream rows directly to the client to avoid memory exhaustion.
- **Compatibility:** Exported workbooks must perfectly mimic the exact layout, headers, and formulas of the legacy Excel files to ensure external vendors and legacy third-party macros don't break.

---

## 9. Compatibility Strategy

To ensure zero disruption for operators:
- The UI layer (HTML/JS) will remain entirely untouched during Stage 1 and 2.
- The `core/views/*.py` controllers will be refactored to use an abstract interface (e.g., `get_active_ftl_data()`), which will swap its backend from the Excel parser to the Django ORM via a feature flag.
- The Operations Center `Providers` will be cleanly updated to issue SQL `COUNT(*)` queries instead of file stats, maintaining identical dashboard UI.

---

## 10. Risks & Mitigations

- **Data Quality Migration Risk:** Legacy spreadsheets contain misspellings (e.g., "John doe", "john Doe"). Normalizing these to a single `Driver` table foreign key will fail.  
  *Mitigation:* The Importer will utilize a fuzzy-matching staging table. Unresolved foreign keys will trigger a manual mapping UI in the Django Admin before they are promoted to the live `Shipment` table.
- **Asynchronous Lag:** If imports run in the background (Celery), users might refresh the page and not see their uploaded data.  
  *Mitigation:* Implement real-time progress indicators on the frontend polling the `ImportJob` status.

---

## 11. Rollback Strategy

The migration is fully reversible at every stage prior to Final Cutover.
- **Rollback Triggers:** Widespread `ImportErrorRecord` spikes, PostgreSQL CPU saturation, or incorrect data rendering in the portal.
- **Execution:** Because the architecture retains the `media/` file uploads (Archival strategy), reverting simply requires flipping the feature flag back to the `ExcelProvider` interface. The database can be wiped and re-imported from the archives once the bug is resolved.

---

## 12. Future Roadmap Alignment

This ADR serves as the necessary foundation for all future roadmap phases:
- **Phase 3 (Shipment Domain):** Executes the Domain Model Design outlined in Section 4. (This is where PostgreSQL schemas are implemented).
- **Phase 4 (Workbook Simplification):** Retires the code paths deprecated by Section 6 (Cutover).
- **Phase 5 (Production Infrastructure):** Scales the infrastructure supporting PostgreSQL (e.g. connection pooling, Redis queues) for production load.
- **Phase 6 (Shipment Tracking API):** The PostgreSQL schema allows simple DRF (Django Rest Framework) serialization, which is impossible with the current Excel architecture.
- **Phase 9 (Analytics):** Normalized data enables instantaneous SQL aggregations for executive dashboards.

---

## 13. Out of Scope

ADR-001 intentionally excludes the following architectural areas to prevent scope creep:
- **Shipment Tracking API:** Design and implementation.
- **Fleet Management:** Implementation of maintenance, fuel, and telemetry tracking.
- **AI Platform:** Machine learning data pipelines.
- **Analytics:** BI tools and dashboard implementation.
- **Production Deployment:** Concrete infrastructure choices (e.g. AWS vs. GCP) and deployment orchestration.
- **Hosting:** Web server and WSGI/ASGI configurations.

---

## 14. Phase 3 Readiness Checklist

Before Phase 3 begins, this architectural gate must be passed:
- [x] ADR approved
- [x] Domain models approved
- [x] Migration strategy approved
- [x] Rollback strategy approved
- [x] Success criteria approved
- [x] Graphify review completed

Phase 3 is fully unblocked once this gate is formalized.

---
*End of ADR-001*
