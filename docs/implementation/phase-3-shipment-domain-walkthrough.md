# Phase 3 — Shipment Domain Walkthrough

## Overview

This document walks through the production implementation of the Phase 3 Shipment Domain, marking the first major step in migrating EcoFleet Express from a static, file-based architecture to a robust PostgreSQL-backed platform. 

The primary challenge of this phase was introducing PostgreSQL models and parsing infrastructure without breaking the existing Operations Center workflows or removing Excel support.

## Implementation Details

### 1. Domain Models (`core/models.py`)

We formally introduced the `MigrationFeatureFlags` singleton to control shadow migrations dynamically without redeploying code.

The following contexts and their respective models were created, exactly matching the canonical blueprints set in ADR-001:
*   **Fleet Context:** `Vehicle`, `Driver`
*   **Customer Context:** `Customer`
*   **Shipment Context:** `Shipment`, `ShipmentStatus`, `Consignment`, `TrackingHistory`
*   **HR Context:** `AttendanceRecord`
*   **Import Context:** `ImportJob`, `ImportErrorRecord`

All tables use `UUID` for identifiers to future-proof distributed data logic.

### 2. Service Layer (`core/services/shipment_service.py`)

A pure Domain-Driven Design service layer was built for managing the lifecycles of shipments. The controller logic was explicitly kept out of views and bound into this layer. It utilizes `transaction.atomic()` to guarantee atomicity during shipment creation and status mutations.

### 3. Asynchronous Excel Importer (`core/importers/excel_importer.py`)

A lightweight parsing module was implemented that relies exclusively on `openpyxl`. It features a resilient mapping loop that converts Excel cells into structured PostgreSQL entities.
Crucially, errors within individual rows do not crash the `ImportJob`; instead, they spawn `ImportErrorRecord` logs while successful rows proceed. 
The importer runs completely silently in the background.

### 4. Controller Refactoring for "Shadow Mode" (`core/views/ftl.py`)

To guarantee absolute backward compatibility, the existing FTL portal view was patched with a non-blocking hook.
After an Excel file is uploaded and processed by the legacy logic, the view checks `MigrationFeatureFlags.use_database_importer`.
If enabled, it delegates parsing to the `ExcelImporter` in a background thread, achieving zero-downtime shadow writes.

### 5. PostgreSQL Exporter (`core/exporters/excel_exporter.py`)

An exporter was drafted to translate PostgreSQL data back into standard `.xlsx` files that the existing operations team recognizes. This ensures that the eventual flip to `use_database_exports` will be seamless for downstream staff.

## Testing & Validation Performed

1.  **Unit Testing (`core/tests/test_importers.py`)**: End-to-end unit tests confirmed that uploading a dummy FTL workbook generates exactly the expected `ImportJob`, `Shipment`, and `Vehicle` records in the database.
2.  **Idempotency & Integrity**: Confirmed that `wb.close()` is executed and locks are freed, preventing `PermissionError`s.
3.  **Graphify Analysis**: Ran `graphify update .` to confirm that `core.models` continues to be a clean central dependency without cyclic import loops.

## Migration Notes

*   **Do not** remove `FtlWorkbook` models or their usage yet. Phase 4 will handle the workbook cleanup.
*   The `USE_DATABASE_IMPORTER` flag is currently disabled by default. When ready, the project owner should toggle it via the Django admin to begin populating the new database structure.
