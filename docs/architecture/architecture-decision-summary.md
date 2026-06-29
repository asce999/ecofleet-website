# Architecture Decision Summary

**Phase:** 2 (ADR-001)  
**Date:** 2026-06-30

## Executive Summary

Phase 2 establishes the canonical architectural blueprint for EcoFleet Express's transition from an Excel-centric system to a robust, relational PostgreSQL-backed architecture. This transition is critical to unlock horizontal scalability, eliminate file-locking bottlenecks, and enforce strict relational data integrity across Shipment, Fleet, and HR bounded contexts.

---

## Major Decisions

1. **Target Database Engine:** PostgreSQL will serve as the sole source of truth for operational data (introduced in Phase 3).
2. **Role of Excel:** Excel is strictly transitioned into an Import/Export format. It will no longer serve as an operational database.
3. **Data Normalization:** Operations data will be structured using 3NF for core entities and `JSONB` for flexible metadata.
4. **Migration Pattern:** A Strangler Fig pattern supported by a Feature Flag Strategy (`USE_DATABASE_IMPORTER`, `USE_DATABASE_READS`) will be used to ensure a zero-downtime transition.
5. **Domain boundaries:** The system is explicitly separated into Shipment, Fleet, HR, Customer, Import, and Export Bounded Contexts.

---

## Trade-offs

- **Why not optimize Python Excel Parsing? (Rejected)**
  - *Trade-off:* While using faster libraries like `pandas` would solve the performance issue, it would not solve the data integrity and relational mapping limitations of Excel. We chose database correctness over minor speed patches.
- **Why not NoSQL? (Rejected)**
  - *Trade-off:* Logistics data is inherently relational (e.g., Drivers assigned to Vehicles assigned to Shipments). NoSQL's schema-less nature does not enforce the necessary referential integrity.
- **Why not a Big Bang Migration? (Rejected)**
  - *Trade-off:* A single weekend cutover presents too much business risk if dirty legacy data fails strict SQL schema validation. The phased "Shadow Mode" approach prioritizes safety over immediate completion.

---

## Deferred Decisions

The following architectural decisions are intentionally postponed to later roadmap phases:
- **Background Worker Infrastructure (Phase 5):** The choice between Celery/Redis vs. RQ vs. AWS SQS for processing asynchronous ImportJobs.
- **Connection Pooling (Phase 5):** PgBouncer configurations for production loads.
- **Analytics Engine (Phase 9):** Choice of BI tool (e.g., Metabase vs. Superset) and materialized views vs. Data Warehouse (Redshift/Snowflake).

---

## Future Dependencies

- **Shipment Tracking API:** The API specification and schema extensions for real-time tracking will be provided directly by the project owner during **Phase 6**.
- **Production Hosting:** All final production infrastructure and web-server configurations (e.g., AWS EC2, Nginx, Gunicorn) will be supplied by the project owner after confirmation from **SVP Infotech** during **Phase 7**.

---

## Roadmap Alignment

This architecture decision summary underpins the entire future roadmap:
- **Phase 3:** Executes the domain model and introduces the PostgreSQL schemas.
- **Phase 4:** Leverages the new models to retire the old workbook code.
- **Phase 5:** Hardens the underlying infrastructure (Redis, PostgreSQL tuning) for production load.
- **Phase 6:** Builds the DRF APIs on top of the strict PostgreSQL relationships defined here.
- **Phase 7+:** Deploys the architecture and enables downstream ML/Analytics.

The architecture remains deployment-agnostic and explicitly avoids scope creep into future phases.
