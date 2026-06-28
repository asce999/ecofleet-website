# Phase 11A: Deployment & Production Hardening (Technical Findings)

---

## DEPLOY-001: Missing WSGI Production Server
**Severity:** High
**Confidence:** Confirmed
**Business Criticality:** Business Critical

**Affected Components:**
- Deployment (`requirements.txt`)
- Execution Environment

**Evidence:**
- File: `requirements.txt`
- Code: Gunicorn, uWSGI, Waitress, and Daphne are entirely absent from the dependency list.

**Technical Description:**
The application dependencies do not include a production WSGI or ASGI server. This implies the deployment relies on Django's built-in `python manage.py runserver`. The built-in server is explicitly designed for local development only. It is single-threaded (blocking all other users while processing a workbook), handles static files inefficiently, and has not been subjected to security audits for handling malformed HTTP requests.

**Business Impact:**
If deployed using `runserver`, the application will suffer from severe performance bottlenecks (one request processed at a time) and is vulnerable to denial-of-service (DoS) attacks from malformed HTTP headers.

**Root Cause:**
- Deployment

**Why this is a Production Hardening Issue:**
- **Code Evidence:** Absence of `gunicorn` in `requirements.txt`.
- **Deployment Impact:** Precludes containerized deployment (e.g., Docker) from using a robust entrypoint.
- **Operational Impact:** Horrible concurrency; a 10-second FTL workbook upload will lock the server for all other users.

**Cross-Phase References:**
- Phase 4: Upload Processing (where blocking operations occur).

**Counter Argument:**
The server administrators might install `gunicorn` globally on the host operating system rather than via `requirements.txt`. However, standard Python deployment practices dictate all application dependencies should be pinned in the repository.

**Confidence Review:**
Confirmed. Standard deployment dependencies are demonstrably missing.

**Exploit Complexity:** Low (DoS via connection exhaustion).
**Detection Difficulty:** Easy (Application hangs).

---

## DEPLOY-002: Missing CSRF_TRUSTED_ORIGINS for Proxy Deployment
**Severity:** High
**Confidence:** Confirmed
**Business Criticality:** Important

**Affected Components:**
- Settings (`ecofleet/settings.py`)
- Security (CSRF Middleware)

**Evidence:**
- File: `ecofleet/settings.py` (Line 313)
- Configuration: `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` is set, but `CSRF_TRUSTED_ORIGINS` is completely absent from the file.

**Technical Description:**
The application configures `SECURE_PROXY_SSL_HEADER` and `CSRF_COOKIE_SECURE`, indicating an architectural intention to deploy behind a reverse proxy (like Nginx or an AWS ALB) terminating HTTPS. However, modern Django's CSRF middleware strictly validates the `Origin` and `Referer` headers against the host for HTTPS requests. When deployed behind a proxy, if the production domain is not explicitly listed in `CSRF_TRUSTED_ORIGINS` (e.g., `['https://production-domain.com']`), the CSRF middleware will reject all `POST` requests.

**Business Impact:**
Upon deploying to production behind an HTTPS proxy, all form submissions (logins, workbook uploads) will fail with a 403 CSRF Verification Failed error, rendering the application entirely unusable.

**Root Cause:**
- Configuration

**Why this is a Production Hardening Issue:**
- **Code Evidence:** Missing `CSRF_TRUSTED_ORIGINS` variable in settings.
- **Deployment Impact:** Causes immediate, catastrophic deployment failure on Day 1.
- **Operational Impact:** Frustrating debugging loop for the DevOps team.

**Counter Argument:**
If the application is deployed directly to the internet without a proxy (e.g., Gunicorn binding to port 443 directly), this setting is not strictly required. However, the presence of `SECURE_PROXY_SSL_HEADER` contradicts this.

**Confidence Review:**
Confirmed based on Django's strict CSRF proxy requirements.

**Exploit Complexity:** N/A (It breaks the app for legitimate users).
**Detection Difficulty:** Easy (Every POST fails).

---

## DEPLOY-003: Single-Node Stateful Architecture
**Severity:** Medium
**Confidence:** Confirmed
**Business Criticality:** Business Critical

**Affected Components:**
- Settings (`DATABASES`, `CACHES`, `MEDIA_ROOT`)
- Storage (File System)

**Evidence:**
- File: `ecofleet/settings.py`
- Configuration:
  - `DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'`
  - `CACHES['default']['BACKEND'] = 'django.core.cache.backends.filebased.FileBasedCache'`
  - `MEDIA_ROOT = BASE_DIR / 'media'`

**Technical Description:**
The application relies entirely on local file-system state. The database is SQLite, the cache is FileBasedCache, and media (uploaded workbooks) are stored directly on the server's disk. This architecture creates a strictly stateful, single-node application. 

**Business Impact:**
1. **Data Loss:** If deployed to ephemeral container environments (like AWS ECS, Kubernetes, or Heroku), all uploaded files, user accounts, and tool runs will be permanently destroyed when the container restarts.
2. **No Scaling:** The application cannot be scaled horizontally. If load increases and a second server is spun up, the two servers will have completely independent databases and file storage, leading to split-brain data corruption.

**Root Cause:**
- Technical Debt / Operational Assumption

**Why this is a Production Hardening Issue:**
- **Code Evidence:** Hardcoded paths to `BASE_DIR`.
- **Deployment Impact:** Restricts the application to a single, monolithic Virtual Machine (EC2 instance) with a persistent attached volume (EBS).
- **Operational Impact:** Backup and disaster recovery strategies must rely on whole-VM snapshots rather than automated managed services (like AWS RDS or S3).

**Counter Argument:**
For a small internal logistics tool, a single VM running SQLite is extremely cost-effective and perfectly valid, provided the VM's disk is aggressively backed up.

**Confidence Review:**
Confirmed. The architecture explicitly binds the application to local disk state.

**Exploit Complexity:** N/A
**Detection Difficulty:** N/A

---

## DEPLOY-004: Insecure SSL Redirect Default
**Severity:** Medium
**Confidence:** Confirmed
**Business Criticality:** Important

**Affected Components:**
- Settings (`ecofleet/settings.py`)
- Environment (`.env.example`)

**Evidence:**
- File: `ecofleet/settings.py` (Line 309)
- Code: `SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'`
- File: `.env.example` (Line 4)
- Code: `SECURE_SSL_REDIRECT=False`

**Technical Description:**
The application correctly allows enabling `SECURE_SSL_REDIRECT` via an environment variable. However, it defaults to `False` in code, and the provided `.env.example` also explicitly sets it to `False`. While this is necessary for local development, it creates a dangerous "fail-open" scenario for production. If the DevOps engineer forgets to explicitly flip this boolean to `True` during deployment, the application will silently accept and serve traffic over plaintext HTTP.

**Business Impact:**
If deployed without the flag, employee credentials and sensitive supply chain data will be transmitted in plaintext, neutralizing the protection provided by the `SECURE_HSTS_SECONDS` header (since HSTS requires an initial HTTPS connection).

**Root Cause:**
- Operational Assumption

**Why this is a Production Hardening Issue:**
- **Code Evidence:** The default fallback value is `'False'`.
- **Deployment Impact:** Requires perfect execution by the deployment team to achieve security.
- **Operational Impact:** Silent downgrade of transport security.

**Counter Argument:**
The reverse proxy (Nginx/ALB) is usually responsible for redirecting HTTP to HTTPS at the edge, meaning Django never even sees the HTTP traffic. If the infrastructure handles the redirect, this setting is redundant.

**Confidence Review:**
Confirmed. Relying on infrastructure is common, but defense-in-depth requires the framework to also enforce the redirect.

**Exploit Complexity:** Low (Passive network sniffing if deployed incorrectly).
**Detection Difficulty:** Easy

---

## DEPLOY-005: Misconfigured Referrer Policy Header
**Severity:** Low
**Confidence:** Confirmed
**Business Criticality:** Minor

**Affected Components:**
- Settings (`ecofleet/settings.py`)
- Security Middleware

**Evidence:**
- File: `ecofleet/settings.py` (Line 303)
- Code: `REFERRER_POLICY = 'same-origin'`

**Technical Description:**
The configuration attempts to set the Referrer-Policy header using `REFERRER_POLICY = 'same-origin'`. However, Django's `SecurityMiddleware` expects the setting to be named `SECURE_REFERRER_POLICY`. Because the variable name is incorrect, the middleware ignores it entirely.

**Business Impact:**
The intended Referrer-Policy is not applied. (Note: Django 6.0 defaults to `same-origin` internally even if unset, so the practical risk is mitigated by the framework's secure defaults, but the misconfiguration demonstrates a lack of deployment QA).

**Root Cause:**
- Configuration

**Why this is a Production Hardening Issue:**
- **Code Evidence:** Incorrect variable name.
- **Deployment Impact:** None (Framework defaults save it).
- **Operational Impact:** None.

**Confidence Review:**
Confirmed. The variable name is verifiably incorrect according to Django documentation.

**Exploit Complexity:** N/A
**Detection Difficulty:** N/A

---

## DEPLOY-006: Highly Secure X-Accel-Redirect Implementation (Informational)
**Severity:** Informational
**Confidence:** Confirmed
**Business Criticality:** Minor

**Affected Components:**
- Views (`core/views/media.py`)
- Settings (`ecofleet/settings.py`)

**Evidence:**
- File: `core/views/media.py` (Lines 24-29)
- Code: 
  ```python
  if getattr(settings, 'NGINX_ACCEL_REDIRECT', False):
      response = FileResponse(open(requested, 'rb'))
      response['X-Accel-Redirect'] = '/protected-media/' + path
  ```

**Technical Description:**
The application implements an advanced deployment pattern for serving protected media files. Rather than forcing Django to stream heavy Excel files through the Python WSGI layer (which blocks worker threads), the `protected_media` view validates the user's authorization and then delegates the actual file transfer back to Nginx using the `X-Accel-Redirect` header.

**Business Impact:**
This provides the best of both worlds: strict, application-layer access control over sensitive generated workbooks, combined with the extreme performance and memory efficiency of Nginx for static file delivery.

**Root Cause:**
- Configuration (Positive)

**Why this is a Production Hardening Issue:**
- **Code Evidence:** Proper use of the `X-Accel-Redirect` header triggered via a deployment environment variable (`NGINX_ACCEL_REDIRECT`).
- **Deployment Impact:** Allows for highly scalable file serving in production.
- **Operational Impact:** Prevents Gunicorn worker exhaustion during mass report downloads.

**Cross-Phase References:**
- Phase 6: Authorization (Protecting the files).

**Confidence Review:**
Confirmed. Excellent architectural decision.
