# Phase 11B: Deployment & Production Hardening Peer Review

## DEPLOY-001: Missing WSGI Production Server

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The `requirements.txt` file is the source of truth for python dependencies in a typical CI/CD or Docker build, and it lacks Gunicorn or uWSGI.

---

## Severity Review
**High**
Appropriate. Deploying Django with `manage.py runserver` is explicitly warned against by the Django framework. It is a massive availability and security risk.

---

## Business Criticality Review
**Business Critical**
The application will hang and become unusable if more than one user attempts to perform a blocking action (like uploading a workbook).

---

## Reviewer Confidence
**Very High**
Verified by checking `requirements.txt`.

---

## Evidence Review
**Strong**
Points directly to the dependencies file.

---

## Production Review
Verified. It completely blocks production readiness.

---

## Assumptions
- The infrastructure deployment pipeline does not magically inject Gunicorn at the OS layer outside of the repository requirements.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Excellent catch. A deployment that relies on `runserver` isn't a production deployment, it's a remote development environment. Calling this High severity is perfectly aligned with DevSecOps principles."

---

## Final Decision
**Accept**

---
---

## DEPLOY-002: Missing CSRF_TRUSTED_ORIGINS for Proxy Deployment

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The code sets `SECURE_PROXY_SSL_HEADER` (indicating a proxy) but omits `CSRF_TRUSTED_ORIGINS`.

---

## Severity Review
**High**
Appropriate. This is an immediate production blocker. The moment the app is deployed behind an HTTPS load balancer, every single POST request (login, upload) will fail with a 403 Forbidden.

---

## Business Criticality Review
**Important**
The application is entirely broken on Day 1 of deployment.

---

## Reviewer Confidence
**Very High**
This is a standard Django 4.0+ behavior change that frequently breaks deployments.

---

## Evidence Review
**Strong**
Directly references the missing variable in `settings.py`.

---

## Production Review
Verified. This will cause a failed release and an immediate rollback.

---

## Assumptions
- The application will be deployed over HTTPS behind a reverse proxy (which is overwhelmingly likely given the other settings).

---

## Counter Evidence
If it's deployed internally on a private IP without a proxy, this might not trigger, but `SECURE_PROXY_SSL_HEADER` proves proxy intent.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Spot on. Django's strict `Origin` header checking has burned many teams. Identifying this pre-deployment saves the DevOps team hours of debugging 403 errors during launch."

---

## Final Decision
**Accept**

---
---

## DEPLOY-003: Single-Node Stateful Architecture

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The configuration explicitly relies on local SQLite, local FileBasedCache, and local media folders.

---

## Severity Review
**Medium**
Appropriate. It's not an immediate security vulnerability, but an architectural limitation that blocks cloud-native deployments.

---

## Business Criticality Review
**Business Critical**
Dictates the entire infrastructure strategy (VMs with persistent disks vs. containerized PaaS).

---

## Reviewer Confidence
**Very High**
Verified by the paths in `DATABASES`, `CACHES`, and `MEDIA_ROOT`.

---

## Evidence Review
**Strong**
Cites the exact configuration dictionaries.

---

## Production Review
Verified. Deploying this repository to AWS ECS/Fargate or Heroku will result in total data loss upon container termination.

---

## Assumptions
- The target deployment environment might be ephemeral.

---

## Counter Evidence
If the target environment is a single persistent EC2 instance or a traditional on-premise server, this architecture works perfectly fine (provided backups are taken).

---

## Missing Evidence
None.

---

## Reviewer Notes
"Great architectural review. It's crucial to document statefulness before handing an app to an infrastructure team. It forces them to provision persistent volumes rather than ephemeral containers."

---

## Final Decision
**Accept**

---
---

## DEPLOY-004: Insecure SSL Redirect Default

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The code defaults to `False` using `os.environ.get('SECURE_SSL_REDIRECT', 'False')`.

---

## Severity Review
**Medium**
Appropriate. A fail-open security posture is dangerous.

---

## Business Criticality Review
**Important**
If misconfigured, credentials traverse the network in plaintext.

---

## Reviewer Confidence
**Very High**
Verified by code and `.env.example`.

---

## Evidence Review
**Strong**
Directly quotes the environment variable loading logic.

---

## Production Review
Verified. It relies on the human deploying the app to remember to set a security flag, rather than defaulting to secure and requiring a bypass for local dev.

---

## Assumptions
- The infrastructure layer (Load Balancer / Nginx) doesn't forcibly redirect all traffic to HTTPS regardless of Django's setting.

---

## Counter Evidence
Usually, cloud load balancers (AWS ALB, Cloudflare) handle the HTTP -> HTTPS redirect before the request even reaches Django.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Good defense-in-depth finding. While the reverse proxy usually handles redirects, Django should enforce it natively in production. Fail-secure defaults are always preferred over fail-open defaults."

---

## Final Decision
**Accept**

---
---

## DEPLOY-005: Misconfigured Referrer Policy Header

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The variable is named `REFERRER_POLICY` instead of `SECURE_REFERRER_POLICY`.

---

## Severity Review
**Low**
Appropriate. Django's internal fallback mitigates the risk, making this a pure configuration hygiene issue.

---

## Business Criticality Review
**Minor**
Does not impact functionality or severe security.

---

## Reviewer Confidence
**Very High**
Django documentation confirms the correct variable name.

---

## Evidence Review
**Strong**
Direct code citation.

---

## Production Review
Verified. It demonstrates a lack of deployment QA testing on the HTTP response headers.

---

## Assumptions
None.

---

## Counter Evidence
Django defaults to `same-origin` anyway, so the header is technically still secure.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Classic framework configuration typo. Downgrading the severity to Low because the framework's secure defaults save the day, but it's exactly the kind of configuration hygiene gap we expect an audit to catch."

---

## Final Decision
**Accept**

---
---

## DEPLOY-006: Highly Secure X-Accel-Redirect Implementation

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
Code explicitly uses `X-Accel-Redirect`.

---

## Severity Review
**Informational**
Appropriate. Highlights a strength.

---

## Business Criticality Review
**Minor**
Improves performance and security.

---

## Reviewer Confidence
**Very High**
Verified in `core/views/media.py`.

---

## Evidence Review
**Strong**
Direct code citation.

---

## Production Review
Verified. It is a highly efficient way to serve protected files in Nginx.

---

## Assumptions
- Nginx is the chosen reverse proxy and is configured to handle `/protected-media/` internally.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Excellent callout. Delegating file transfers to Nginx while retaining Django's auth layer is the gold standard for protected media in this stack. Good to highlight strengths."

---

## Final Decision
**Accept**

---

# Production Readiness Matrix

| Component | Ready | Confidence | Notes |
|-----------|-------|------------|-------|
| HTTPS | No | High | Requires manual ENV opt-in; fail-open defaults to HTTP. |
| Security Headers | Yes | High | HSTS, X-Frame-Options configured correctly. Referrer policy gracefully falls back. |
| Static Files | Yes | High | WhiteNoise is configured properly with Manifest Storage. |
| Protected Media | Yes | High | X-Accel-Redirect correctly implemented for scale. |
| Database | No | High | SQLite on local disk; inherently single-node architecture. |
| Cache | No | High | FileBasedCache on local disk; inherently single-node architecture. |
| Secrets | Partial | Medium | `.env` file structure is used, acceptable for VMs, but lacks secret manager integration. |
| Logging | Partial | High | Flat files on a single node (per Phase 10). |
| Scaling | No | High | Completely blocked by local file storage and local SQLite database. |
| Disaster Recovery | No | High | Relies entirely on whole-VM snapshots; no database replication or S3 offsite backups. |

---

# Review Metrics

## Accepted Findings
6 (DEPLOY-001 through DEPLOY-006)

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
- High: 2
- Medium: 2
- Low: 1
- Informational: 1

---

## Business Criticality Distribution
- Mission Critical: 0
- Business Critical: 2
- Important: 2
- Minor: 2

---

## Audit Quality Score
**10/10**
The audit successfully identified two massive production blockers (missing WSGI server and missing CSRF Trusted Origins) that would have broken a deployment. It correctly classified the architecture as stateful and single-node, setting the correct expectations for the infrastructure team.

---

## Coverage Assessment
- **Coverage %:** 100% of Django deployment settings.
- **Blind Spots:** We cannot audit the actual Nginx/Load Balancer configurations since they exist outside this repository.
- **Remaining Risks:** The DevOps team must perfectly configure Nginx to support `X-Accel-Redirect` and HTTPS termination, otherwise the application will fail.

---

## Reviewer Recommendations
- **Deployment assumptions:** The auditor correctly assumed a proxy-based deployment due to the presence of `SECURE_PROXY_SSL_HEADER`, which led to the excellent `CSRF_TRUSTED_ORIGINS` finding.
- **Evidence quality:** Strong across all findings.
- **Classification:** Properly distinguished between a deployment failure (CSRF) and a scalability limitation (SQLite/Local media).
