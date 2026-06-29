# EcoFleet Express — Official Engineering Roadmap

> **Status:** Active
>
> This document serves as the **single source of truth** for the engineering roadmap of EcoFleet Express. Every implementation, review, refactor, and feature must align with the current roadmap phase unless explicitly approved by the project owner.

---

# Phase 1 — Sprint C: Engineering Stabilization

## Objective

Complete all remaining engineering improvements identified during the Principal Engineering Review before introducing major architectural changes or new features.

---

## Tasks

### Correctness

* Fix the missing `messages` import in authorization failure paths.
* Verify all permission error paths.
* Add regression tests for authorization failures.
* Remove any remaining correctness issues identified during code review.

---

### Transaction Safety

* Implement `transaction.atomic()` where required.
* Ensure workbook activation/deactivation is atomic.
* Prevent partial database updates.
* Introduce partial unique constraints for active workbooks.
* Enforce a single active workbook per workbook type.

---

### Workbook Reliability

* Replace direct workbook saves with atomic save operations.
* Implement temporary workbook creation.
* Replace files using `os.replace()`.
* Validate workbook integrity before replacing.
* Improve error handling during workbook persistence.

---

### Workbook Locking

* Add PID ownership.
* Add timestamps.
* Add stale-lock detection.
* Add automatic stale-lock recovery.
* Add timeout handling.
* Improve lock reliability.

---

### Testing

* Expand workbook tests.
* Expand salary calculation tests.
* Add workbook write tests.
* Add workbook activation tests.
* Add locking tests.
* Add provider tests.
* Add regression tests.
* Remove scratch tests from production test suite.

---

### Documentation

* Improve README.
* Improve `.env.example`.
* Improve project setup documentation.
* Improve development workflow documentation.
* Improve architecture documentation.

---

### Deliverables

* Engineering stabilization complete.
* Correctness issues resolved.
* Reliability improvements completed.
* Expanded automated testing.
* Updated documentation.

---

# Phase 2 — ADR-001: Operational Data Migration

## Objective

Create the architectural blueprint for migrating operational data from Excel to PostgreSQL.

---

## Tasks

* Document the current workbook architecture.
* Explain why Excel is no longer suitable as the operational database.
* Define PostgreSQL as the new source of truth.
* Define migration strategy.
* Define rollback strategy.
* Define import workflow.
* Define export workflow.
* Define compatibility strategy.
* Define migration phases.
* Define success criteria.
* Define project risks.
* Define architectural constraints.

---

## Deliverables

* ADR-001
* Migration strategy
* Architecture approval

---

# Phase 3 — Shipment Domain

## Objective

Introduce a relational Shipment Domain while maintaining compatibility with existing Excel workflows.

---

## Tasks

### Domain Models

Design and implement:

* Shipment
* Shipment Status
* Shipment Events
* Tracking History
* Customer
* Consignment
* Vehicle
* Driver
* Delivery Status
* Shipment Notes

---

### Database

* Design relational schema.
* Normalize data.
* Create migrations.
* Create indexes.
* Add constraints.
* Add validation.
* Implement repository/services.

---

### Excel Integration

* Build shipment importer.
* Build shipment exporter.
* Preserve workbook compatibility.
* Create migration tools.
* Validate imported data.
* Build reconciliation tools.

---

### Portal

* Connect existing portal to Shipment database.
* Maintain existing user workflow.
* Ensure zero disruption during migration.

---

### Deliverables

* Shipment database.
* Import/export system.
* Migration utilities.
* Fully operational Shipment Domain.

---

# Phase 4 — Workbook Simplification

## Objective

Remove duplicated workbook logic after Shipment migration is complete.

---

## Tasks

### Architecture

Create:

* WorkbookService
* WorkbookAdapter
* WorkbookImporter
* WorkbookExporter
* Shared Workbook Utilities

---

### Refactoring

Remove duplicated logic from:

* BTPL
* FTL
* Attendance
* COF

---

### Improvements

* Shared parsing.
* Shared validation.
* Shared pagination.
* Shared preview generation.
* Shared caching.
* Shared workbook utilities.

---

### Testing

* Validate all workbook operations.
* Ensure backward compatibility.

---

### Deliverables

* Shared workbook engine.
* Significantly reduced code duplication.
* Simplified workbook maintenance.

---

# Phase 5 — Production Infrastructure

## Objective

Modernize infrastructure for production deployment.

---

## Tasks

### Database

* Migrate to PostgreSQL.
* Configure production database.
* Optimize indexes.
* Verify migrations.

---

### Cache

* Replace FileBasedCache with Redis.
* Configure production caching.
* Improve cache invalidation.
* Improve performance.

---

### Background Processing

Implement:

* Celery (or equivalent)
* Redis Broker
* Background jobs
* Scheduled tasks
* Queue monitoring

---

### Observability

* Request IDs.
* Structured logging.
* Audit improvements.
* Monitoring.
* Health checks.
* Metrics.
* Performance monitoring.

---

### Security

* Production security validation.
* CSP improvements.
* SSL verification.
* Production configuration review.

---

### Deliverables

* PostgreSQL.
* Redis.
* Background task processing.
* Production-ready infrastructure.

---

# Phase 6 — Shipment Tracking API

## Objective

Expose shipment data through a secure, scalable REST API.

---

## Important

The complete Shipment Tracking API specification will be provided by the project owner.

No assumptions should be made before receiving official API documentation.

---

## Tasks

### API Design

* Design API architecture.
* Design versioning.
* Define authentication.
* Define authorization.
* Define request validation.
* Define error handling.

---

### Endpoints

Implement:

* Shipment lookup.
* Shipment status.
* Tracking history.
* Search.
* Filtering.
* Pagination.
* Status updates.
* Webhook support (if applicable).

---

### Security

* Authentication.
* Authorization.
* Rate limiting.
* Validation.
* API documentation.

---

### Integration

* Integrate third-party shipment provider.
* Handle retries.
* Handle failures.
* Handle synchronization.

---

### Deliverables

* Shipment Tracking API.
* API documentation.
* Integration complete.

---

# Phase 7 — Production Deployment

## Objective

Deploy EcoFleet Express into production.

---

## Important

Production hosting details will be provided by the project owner after confirmation from **SVP Infotech**.

Do not make assumptions regarding:

* Hosting provider
* Server architecture
* Operating system
* Reverse proxy
* SSL
* Infrastructure

---

## Tasks

* Configure production environment.
* Configure environment variables.
* Configure backups.
* Configure health checks.
* Configure monitoring.
* Configure deployment process.
* Configure rollback strategy.
* Verify production readiness.

---

## Deliverables

* Production deployment.
* Production documentation.
* Deployment guide.

---

# Phase 8 — Fleet Management

## Objective

Introduce complete fleet management functionality.

---

## Tasks

### Vehicles

* Vehicle management.
* Vehicle assignments.
* Vehicle history.
* Vehicle documentation.
* Vehicle maintenance.

---

### Drivers

* Driver management.
* Driver assignments.
* Driver documents.
* Driver availability.
* Driver performance.

---

### Trips

* Trip management.
* Route management.
* Assignments.
* Scheduling.
* Trip history.

---

### Fuel

* Fuel tracking.
* Fuel reports.
* Fuel analytics.

---

### Deliverables

* Fleet Management Module.

---

# Phase 9 — Analytics

## Objective

Leverage relational data for operational and executive analytics.

---

## Tasks

* Operational dashboards.
* Shipment analytics.
* Fleet analytics.
* Driver analytics.
* Financial analytics.
* Executive dashboards.
* KPI reporting.
* Trend analysis.
* Performance reports.
* Exportable reports.

---

## Deliverables

* Analytics Platform.

---

# Phase 10 — AI Platform

## Objective

Introduce AI-powered operational intelligence.

---

## Tasks

### AI Features

* ETA prediction.
* Delay prediction.
* Route optimization.
* Cost optimization.
* Shipment recommendations.
* Operational insights.
* Predictive analytics.
* AI assistant for Operations Center.
* Intelligent reporting.

---

### Future Enhancements

* Forecasting.
* Demand prediction.
* Capacity planning.
* Automated recommendations.
* AI-powered monitoring.

---

## Deliverables

* AI Platform.

---

# Continuous Requirements (Every Phase)

Every phase must include:

* Read and follow `roadmap.md`.
* Read relevant implementation plans.
* Read relevant walkthroughs.
* Read relevant ADRs.
* Preserve Provider Architecture.
* Preserve Operations Center architecture.
* Maintain UI/UX consistency.
* Maintain coding standards.
* Maintain backward compatibility where applicable.
* Update Graphify before implementation.
* Update Graphify after implementation.
* Run Django tests.
* Run Playwright tests.
* Run BetterBugs validation.
* Use Context7 where framework documentation is required.
* Use relevant MCPs, plugins, and skills to maximize implementation quality.
* Update project documentation.
* Generate an implementation report summarizing:

  * Completed work.
  * Remaining work.
  * Blockers.
  * Suggested improvements.
  * Technical debt.
  * Website rating (/10) with detailed justification.
  * Alignment with the roadmap.
* Wait for project owner approval before proceeding to the next roadmap phase.
