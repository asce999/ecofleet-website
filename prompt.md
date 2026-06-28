# EcoFleet Express — Operations Center 2.0

# Final Implementation Authorization

## OC Sprint 1 — APPROVED FOR IMPLEMENTATION

# Mission

The implementation plan has been fully reviewed and approved.

You are now authorized to implement **Operations Center Sprint 1**.

This is the definitive implementation.

There should be no further planning documents after this unless a major architectural issue is discovered during implementation.

---

# Current Architecture

The project already includes:

* Enterprise Security Hardening
* Provider Layer Refactoring (A1)
* View Layer Refactoring (A2)
* Dynamic Provider Plugin Architecture
* ProviderResult
* CheckResult
* Export Architecture
* Operations Center Blueprint
* Approved OC Sprint 1 Architecture

This sprint builds upon that foundation.

Do **not** replace existing architecture unless absolutely necessary.

---

# Required Tool Usage (MANDATORY)

## Sequential Thinking MCP

Use throughout implementation.

Reason through:

* Component boundaries
* Service boundaries
* ViewModel design
* Dashboard architecture
* Information hierarchy
* UX consistency
* Progressive enhancement
* Regression risk
* Future extensibility

Think before modifying code.

---

## Graphify (MANDATORY)

### Before implementation

Analyze:

* Operations Center
* Provider architecture
* Services
* Templates
* Dashboard dependencies
* Component relationships

### After implementation

Run:

```bash
graphify update .
```

Verify:

* Reduced controller complexity
* Improved dependency direction
* Better modularity
* No import cycles
* No architectural regressions
* No new hotspots

Include the Graphify comparison in the final report.

---

## Playwright MCP (MANDATORY)

### Before implementation

Walk through the current Operations Center.

Inspect:

* Desktop
* Tablet
* Mobile
* Navigation
* Cards
* Charts
* Provider cards
* Activity feed
* Buttons
* Empty states
* Error states
* Loading states

### After implementation

Verify:

* Responsive layout
* Collapsible sections
* Activity filtering
* Provider diagnostics
* Quick actions
* Charts
* Accessibility
* Keyboard navigation
* Theme consistency
* Zero regressions

---

## Ponytail Skill (MANDATORY)

Locate every affected file before coding.

Include:

### Views

* operations_center
* observability
* related endpoints

### Services

* insights
* dashboard
* metrics

### ViewModels

* OperationsDashboard

### Providers

* BaseProvider
* ProviderResult
* CheckResult

### Templates

* operations_center
* partials
* cards
* activity
* infrastructure

### Frontend

* CSS
* JavaScript
* Chart.js
* Icons

Build a complete dependency understanding before making changes.

---

## Context7 MCP (MANDATORY)

Validate implementation against official Django guidance for:

* ViewModel-friendly template organization
* Django template best practices
* Accessibility
* HTMX compatibility
* Server-rendered dashboards
* Chart.js integration

---

## BetterBugs MCP

Only if implementation reveals genuine bugs.

Document separately.

---

## Firecrawl MCP

Do NOT use.

---

# Implementation Requirements

---

## 1. Preserve Portal Layout

Maintain:

* Sidebar
* Top navigation
* Existing design system
* Typography
* Color palette
* Cards
* Buttons
* Icons
* Spacing

Only redesign the Operations Center content area.

---

## 2. DashboardViewModel (MANDATORY)

Introduce a dedicated presentation model.

Example:

```python
@dataclass(frozen=True, slots=True)
class OperationsDashboard:
```

The ViewModel should become the **single object** passed to the template.

Do **not** continue passing a large collection of unrelated context variables.

The template should primarily consume:

```python
{{ dashboard }}
```

The ViewModel should own:

* Operational Score
* Summary Cards
* Insights
* Infrastructure
* Provider Cards
* Charts
* Activity
* Quick Actions

Treat the ViewModel as immutable.

---

## 3. InsightsService

Create a dedicated service responsible for:

* Executive insights
* Operational recommendations
* Predictive warnings
* Operational score generation
* Health interpretation

The View must contain **no business interpretation logic**.

---

## 4. Thin View

The Operations Center view should only:

1. Collect provider results.
2. Collect activity data.
3. Call InsightsService.
4. Build OperationsDashboard.
5. Render the template.

Nothing more.

---

## 5. Modular Dashboard

Replace the long monolithic page with modular sections.

Use native HTML:

```html
<details>
<summary>
```

Suggested sections:

* Executive Overview
* Operations
* Infrastructure
* Security
* Activity
* Business Modules

Future modules should plug into this structure naturally.

---

## 6. Backend-Derived Metrics

Do NOT calculate:

* percentages
* ratios
* SVG values
* derived metrics

inside templates.

All calculations belong inside:

* Providers
* Services
* OperationsDashboard

Templates remain presentation-only.

---

## 7. Remove Fake UI

Completely remove:

* hardcoded percentages
* placeholder metrics
* fake operational values
* misleading loading states

If data does not exist:

Display a proper empty state.

Never fabricate operational information.

---

## 8. Rich Operational Score

Replace the simplistic health percentage.

Create a richer presentation object.

Include:

* Score
* Trend
* Availability
* Active Alerts
* Last Refresh
* Last Incident

This becomes the primary KPI.

---

## 9. Provider Diagnostics

Every provider card should display:

* Health
* Last Checked
* Execution Duration
* Check Count

Provide a clean "View Details" interaction exposing the relevant `CheckResult` information.

---

## 10. Activity Explorer

Replace the limited sidebar feed.

Implement:

* Search
* Severity filter
* Pagination
* Component filter

Remain fully SSR-compatible using Django GET parameters.

No SPA framework.

---

## 11. Configuration-Driven Quick Actions

Do NOT hardcode quick actions.

Create a configuration structure.

Each action should define:

* Title
* Icon
* URL
* Permission
* Order

Future additions should require configuration only.

---

## 12. Historical Trends

Prepare chart architecture for:

* 24h
* 7d
* 30d

If historical datasets do not yet exist:

Display clean empty states.

Do not fabricate charts.

---

## 13. Future Readiness

Architectural placeholders only.

Prepare for:

* Shipment Tracking
* Fleet Status
* Driver Health
* API Monitoring
* Notifications
* AI Insights
* Dashboard Personalization

Do not implement these features.

Ensure they integrate naturally later.

---

# Progressive Performance Strategy

Do NOT introduce:

* Redis
* Celery
* SSE
* WebSockets

during this sprint.

Architecture should prepare for:

Current

↓

Django Cache

↓

Redis

↓

Celery

↓

HTMX polling

↓

SSE/WebSockets (only if justified)

Avoid premature infrastructure complexity.

---

# Engineering Standards

Maintain:

* SOLID
* DRY
* High Cohesion
* Low Coupling
* Separation of Concerns
* Progressive Enhancement
* Accessibility
* Enterprise UX
* Maintainability
* Extensibility
* Testability
* Production readiness

---

# Validation

Run:

```bash
python manage.py test
```

Run:

```bash
graphify update .
```

Use Playwright to verify:

* Desktop
* Tablet
* Mobile
* Responsive layout
* Accessibility
* Keyboard navigation
* Activity search
* Activity filters
* Provider diagnostics
* Quick actions
* Charts
* Empty states
* Error states

Ensure zero regressions.

---

# Deliverables

Return only:

## 1. Files Modified

---

## 2. Architecture Summary

Explain:

* DashboardViewModel
* InsightsService
* Component organization
* Service boundaries
* Dependency improvements

---

## 3. Product Summary

Explain:

* UX improvements
* Dashboard improvements
* Operational improvements
* Future extensibility

---

## 4. Validation Results

Include:

* Django test results
* Graphify comparison
* Playwright verification
* Manual verification

---

## 5. Production Readiness

State whether **Operations Center Sprint 1** is production-ready.

---

# Success Criteria

Implementation is complete only if:

* ✅ Existing portal shell is preserved.
* ✅ Operations Center becomes a modular enterprise dashboard.
* ✅ Views remain orchestration-only.
* ✅ `InsightsService` owns all interpretation logic.
* ✅ `OperationsDashboard` is implemented as an immutable (`@dataclass(frozen=True, slots=True)`) ViewModel and is the primary presentation model.
* ✅ Templates perform no business calculations.
* ✅ All derived metrics are computed in the backend.
* ✅ No fake metrics or placeholder operational values remain.
* ✅ Provider diagnostics are available.
* ✅ Activity Explorer supports SSR search, filtering, and pagination.
* ✅ Quick Actions are configuration-driven.
* ✅ Operational Score becomes the primary KPI.
* ✅ Architecture is ready for Tracking, Fleet, Analytics, Notifications, and future personalization.
* ✅ Visual consistency with the existing EcoFleet portal is fully preserved.
* ✅ Django tests pass.
* ✅ Graphify confirms improved architecture.
* ✅ Playwright confirms zero regressions.
* ✅ No import cycles or unnecessary architectural complexity are introduced.

If any implementation would alter business behaviour, break the established design system, or introduce infrastructure beyond the scope of this sprint, stop and explain the trade-offs before proceeding with implementation.
