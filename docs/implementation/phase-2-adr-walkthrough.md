# Phase 2 ADR Walkthrough

This document serves as an engineering walkthrough for the architectural decisions formulated during **Phase 2: ADR-001 (Operational Data Migration)**. It explains the rationale behind the design, alternative architectures considered, and the long-term implications for EcoFleet Express.

## 1. Architectural Decisions Summarized

**Decision 1: PostgreSQL as the Operational Database**
We are replacing the Excel file system with a relational PostgreSQL schema.
*Reasoning:* PostgreSQL provides native ACID transaction compliance, row-level concurrency without massive file-level locking, and strict relational integrity checking (Foreign Keys, Constraints) out of the box.

**Decision 2: Excel transitions to Import/Export Medium**
*Reasoning:* Users are comfortable with Excel for bulk entry. Completely replacing Excel with web forms for 500-row BTPL manifests would result in user rejection. Therefore, Excel remains as the *ingestion* format, but is no longer queried for real-time application state.

**Decision 3: Strangler Fig Migration Strategy**
We will implement "Shadow Modes" (Dual Write/Read Transition) rather than a "Big Bang" cutover.
*Reasoning:* EcoFleet Express handles active logistical operations. A big bang cutover risks operational downtime if data mismatches occur. Strangler Fig allows us to revert safely by flicking a feature toggle.

## 2. Alternatives Considered & Rejected

### Alternative A: Stick with Excel + SQLite, but optimize Python Parsing
*Concept:* Use `pandas` or `polars` instead of `openpyxl` for faster memory operations, and use advanced locking (e.g., Redis locks).
*Rejection Reason:* This only solves the speed issue, not the data integrity issue. Users can still upload sheets with the wrong column names, or spell "John Doe" differently across sheets, completely breaking analytics and relations.

### Alternative B: NoSQL (MongoDB / DynamoDB)
*Concept:* Store the Excel rows as JSON documents in a NoSQL database for ultimate flexibility.
*Rejection Reason:* EcoFleet's data is highly relational. A `Shipment` belongs to a `Driver`, who has `Attendance`, and is driven by a `Vehicle`. NoSQL makes enforcing these strict referential integrity constraints difficult. We need SQL.

### Alternative C: Immediate Big Bang Migration
*Concept:* Shut down the portal for a weekend, run a massive python script to import all historical Excel files into PostgreSQL, and launch the new Portal UI on Monday.
*Rejection Reason:* Extremely high business risk. Legacy Excel files likely contain thousands of edge cases (corrupted text, missing values) that will cause a strict SQL schema to fail insertion. A phased "Importer" approach allows us to fix these organically over time.

## 3. Engineering Reasoning & Future Implications

By normalizing Master Data (Vehicles, Drivers, Customers) into their own tables:
1. **Reporting becomes instantaneous:** Generating a driver's performance report over the last 12 months becomes a millisecond SQL query (`SELECT ... FROM shipment WHERE driver_id = X AND date > Y`) rather than downloading and iterating through 12 separate monthly FTL Excel sheets.
2. **API Enablement (Phase 6):** Future third-party integrations (e.g., automated tracking hardware in trucks) can hit a DRF REST endpoint `PATCH /api/shipments/{id}/status`. This is trivial with PostgreSQL. It is nearly impossible to safely implement with concurrent Excel files.
3. **AI/ML Enablement (Phase 10):** Machine learning models require structured tabular data. The migration prepares our datasets to be directly ingestible by data engineering pipelines.

## 4. Risks

- **Data Quality during Migration:** The biggest risk is the Importer failing on legacy Excel data due to strict PostgreSQL constraints. 
  *Mitigation:* Use Django's `JSONB` to store raw, unresolved row data if foreign keys fail, and build an "Orphaned Data Resolution" queue in the Django admin for operators to manually correct.

- **Background Queue Dependencies:** The new architecture introduces a background task worker (Celery/Redis) to handle asynchronous imports. This adds infrastructure complexity.
  *Mitigation:* Defer this infrastructure addition to Phase 5. In Phase 3, we can run synchronous imports for small files, and only introduce Celery when absolutely necessary for scaling.
