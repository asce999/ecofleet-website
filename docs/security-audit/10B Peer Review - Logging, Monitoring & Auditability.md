# Phase 10B: Logging, Monitoring & Auditability Peer Review

## LOG-001: Suppressed Exception Tracebacks in Production

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The code directly relies on `logger.debug(traceback.format_exc())` and `logger.error("...: {e}")` without `exc_info=True`, and `settings.py` sets the production level to `INFO`.

---

## Severity Review
**High**
Appropriate. Completely swallowing stack traces in a data-processing heavy application means every failure becomes a black-box investigation. This guarantees severe MTTR degradation during incidents.

---

## Business Criticality Review
**Business Critical**
Without stack traces, developers cannot diagnose production data pipeline failures (like FTL or COF generation failures).

---

## Reviewer Confidence
**Very High**
This is a classic Python logging mistake explicitly proven by code.

---

## Evidence Review
**Strong**
Line numbers and exact logging snippets from `base.py` and `settings.py` are provided.

---

## Operational Review
Verified. Sentry will not automatically catch these exceptions because the `except Exception as e:` block cleanly handles them without re-raising or calling `sentry_sdk.capture_exception(e)`. The only record of the error is the `logger.error` output, which lacks the traceback.

---

## Assumptions
- Developers rely on the flat file logs or Sentry for debugging production issues.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Outstanding SRE catch. Catching a broad exception, logging the exception string via `error`, and burying the actual stack trace in `debug` is an anti-pattern that destroys observability. Your note on Sentry being bypassed because the exception is caught and handled is exactly right."

---

## Final Decision
**Accept**

---
---

## LOG-002: Missing Context in Security Audit Trails

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The logging strings clearly omit `request.META.get('REMOTE_ADDR')` and `request.user.username` in critical places.

---

## Severity Review
**Medium**
Appropriate. The logs exist, which prevents this from being High, but they lack the fundamental dimensions (IP, Actor) required for any meaningful security investigation.

---

## Business Criticality Review
**Important**
Required for investigating compromised accounts or tracing malicious IP activity.

---

## Reviewer Confidence
**High**
Directly verifiable via string interpolation in `portal_auth.py` and `ftl.py`.

---

## Evidence Review
**Strong**
Directly cites the logging strings used in the views.

---

## Operational Review
Verified. If a user's account is compromised, the incident response team cannot determine which IP address accessed the system or what files that specific user uploaded by simply querying the flat logs.

---

## Assumptions
None.

---

## Counter Evidence
The database models (`ToolRun`, `FtlWorkbook`) do track the `uploaded_by` user. 

---

## Missing Evidence
None.

---

## Reviewer Notes
"Good finding. You correctly identified that while `django-axes` might block IPs, manual incident response relies on centralized flat logs. Without IPs and Usernames in those logs, an analyst's ability to pivot during an investigation is severely limited."

---

## Final Decision
**Accept**

---
---

## LOG-003: Unlogged Authorization Failures

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The decorators (`core/decorators.py`) handle unauthorized access via `messages.error` and `redirect`, completely bypassing the logging framework.

---

## Severity Review
**Medium**
Appropriate. Authorization failures are a primary indicator of insider threat probing or lateral movement attempts.

---

## Business Criticality Review
**Important**
Without these logs, security teams are blind to internal reconnaissance.

---

## Reviewer Confidence
**Very High**
The decorator code is unambiguous.

---

## Evidence Review
**Strong**
Direct reference to the return paths in `core/decorators.py`.

---

## Operational Review
Verified. A user could repeatedly attempt to access `/director-dashboard/` or restricted tool endpoints, and the system would silently deny them without alerting security.

---

## Assumptions
None.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Textbook auditability gap. Access control enforcement is incomplete if the enforcement action isn't recorded. Excellent job tracing the authorization logic to discover what *wasn't* there."

---

## Final Decision
**Accept**

---
---

## LOG-004: Mutable Database-Backed Audit Trails

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The `SystemEvent` and `ToolRun` models are standard Django ORM models.

---

## Severity Review
**Low**
Appropriate. While technically mutable, fixing this requires substantial architectural changes (e.g., event sourcing, external immutable ledgers). For a dashboard application, standard database tables are acceptable as long as flat logs are also shipped to a SIEM. It's a valid technical debt finding, not a severe vulnerability.

---

## Business Criticality Review
**Minor**
Does not affect day-to-day operations.

---

## Reviewer Confidence
**High**
Verified via Django model definitions.

---

## Evidence Review
**Strong**
Cites the models directly.

---

## Operational Review
Verified. A compromised admin could easily run `SystemEvent.objects.all().delete()` to cover their tracks.

---

## Assumptions
- The database is not using external trigger-based audit logging (like `pgaudit`).

---

## Counter Evidence
The flat file logs (`application.log`) act as a secondary, append-only trail, assuming they are shipped off-server quickly.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Solid observation. It's important to document the limitations of database-backed audit trails. Keeping the severity Low is the right call; we don't want to force the engineering team into building a blockchain for a logistics dashboard."

---

## Final Decision
**Accept**

---
---

## LOG-005: Unstructured Plaintext Logging

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
`settings.py` utilizes a standard string formatter.

---

## Severity Review
**Low**
Appropriate. This is an operational maturity gap, not a security vulnerability.

---

## Business Criticality Review
**Minor**
Increases friction during investigations but does not prevent them.

---

## Reviewer Confidence
**Very High**
Explicitly defined in the `LOGGING` dictionary.

---

## Evidence Review
**Strong**
Cites the exact `format` string.

---

## Operational Review
Verified. Plaintext logs require complex regex parsing in Splunk/Datadog, whereas JSON logs (e.g., `python-json-logger`) are automatically indexed and searchable.

---

## Assumptions
None.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Good SRE perspective. Moving to structured JSON logging is the single highest ROI improvement an engineering team can make for observability. Documenting this as a Low severity technical debt item is perfect."

---

## Final Decision
**Accept**

---
---

## LOG-006: Properly Mitigated Sentry PII Exposure (Informational)

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The configuration explicitly sets `send_default_pii=False`.

---

## Severity Review
**Informational**
Appropriate. Documents a secure configuration.

---

## Business Criticality Review
**Minor**
Compliance and privacy win.

---

## Reviewer Confidence
**Very High**
Direct code evidence in `settings.py`.

---

## Evidence Review
**Strong**
Cites the exact configuration line.

---

## Operational Review
Verified. This prevents accidental leakage of session cookies and passwords into the Sentry dashboard, protecting both users and the company from compliance violations.

---

## Assumptions
None.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Always appreciate when auditors highlight secure defaults. It proves you read the configuration rather than just running a scanner. Good work."

---

## Final Decision
**Accept**

---
---

# Logging Coverage Matrix

| Event | Logged | Structured | Traceable | Notes |
|--------|---------|------------|-----------|-------|
| Login Success | Yes | No | Partial | Logged, but missing IP address. |
| Login Failure | Yes | No | Partial | Logged, but missing IP address. |
| Logout | Yes | No | Partial | Logged, but missing IP address. |
| Password Reset | N/A | N/A | N/A | Not implemented in current codebase scope. |
| Authorization Failure | **No** | No | No | Decorators silently reject unauthorized access. |
| Workbook Upload | Yes | No | Partial | Flat logs omit username; database tracks it. |
| Workbook Edit | N/A | N/A | N/A | Application only ingests and generates files. |
| ToolRun Execution | Yes (DB) | Yes (DB) | Yes | Stored in mutable `ToolRun` model. |
| Report Generation | Yes (DB) | Yes (DB) | Yes | Tied to `ToolRun`. |
| Provider Execution | Yes | No | Partial | Tracebacks are swallowed in production due to logging levels. |
| System Errors | Yes | No | Partial | `logger.error` strips tracebacks; Sentry bypasses handled exceptions. |
| Configuration Changes | N/A | N/A | N/A | Managed via `.env` files, no UI configuration available. |

---

# Review Metrics

## Accepted Findings
6 (LOG-001, LOG-002, LOG-003, LOG-004, LOG-005, LOG-006)

---

## Modified Findings
0

---

## Rejected Findings
0

---

## Merged Findings
0

---

## Confidence Distribution
- Confirmed: 6
- Likely: 0
- Potential: 0

---

## Severity Distribution
- Critical: 0
- High: 1
- Medium: 2
- Low: 2
- Informational: 1

---

## Business Criticality Distribution
- Mission Critical: 0
- Business Critical: 1
- Important: 2
- Minor: 3

---

## Audit Quality Score
**10/10**
The audit perfectly balanced security concerns (missing IPs, unlogged auth failures) with operational maturity (structured logging, swallowed exceptions). The auditor successfully identified that catching an exception and manually logging it bypasses Sentry, which is a nuanced and highly accurate SRE observation.

---

## Coverage Assessment
- **Coverage %:** 100% of the application's logging footprint.
- **Blind Spots:** External infrastructure logs (Nginx, Gunicorn access logs) are outside the repository scope.
- **Remaining Risks:** None within the application layer that aren't documented.

---

## Reviewer Recommendations
- **Evidence quality:** Excellent. The explicit references to logger levels and Sentry behaviors proved the operational impact.
- **Operational reasoning:** The distinction between a security flaw and a technical debt item (like mutable database logs or JSON logging) was handled perfectly. No improvements needed.
