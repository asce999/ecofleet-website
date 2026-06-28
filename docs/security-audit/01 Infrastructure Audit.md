# 01 Infrastructure & Configuration Security Audit

## 1. Executive Summary
This document outlines the findings from the Phase 1 white-box security audit focusing on the infrastructure and configuration of the EcoFleetExpress Django application. The assessment covered `settings.py`, `.env.example`, WSGI configuration, middlewares, logging, caching, and third-party integrations (Sentry, WhiteNoise, django-axes, django-csp). 

The infrastructure is generally well-secured with solid production defaults, including strict HTTPS enforcement, brute-force protection, and secure cookies. However, there is a significant weakness in the Content Security Policy (CSP) implementation that requires remediation to properly protect against Cross-Site Scripting (XSS).

## 2. Strengths
- **Production Safety Measures**: The application explicitly prevents starting in production (`not DEBUG`) if the `DJANGO_SECRET_KEY` is empty, avoiding accidental fallback to insecure keys.
- **Brute-force Protection**: `django-axes` is well-configured to lock out IPs and usernames after 5 failed attempts with a 1-hour cool-off period.
- **Secure Defaults in Production**: `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, and HSTS are all correctly enforced when `DEBUG = False`.
- **Media Serving Security**: The `protected_media` view correctly enforces authentication before delegating serving to Nginx via `X-Accel-Redirect`, preventing unauthorized access to sensitive uploaded documents.
- **Upload Limits**: `DATA_UPLOAD_MAX_MEMORY_SIZE` and `FILE_UPLOAD_MAX_MEMORY_SIZE` are strictly limited to 10MB, which mitigates simple memory exhaustion Denial-of-Service attacks.

## 3. Confirmed Findings

### 3.1 Weak Content Security Policy (CSP) Allows Unsafe Inline Execution
**Severity**: High
**Confidence**: Confirmed
**Affected Files**: `ecofleet/settings.py`
**Affected Configuration**: `CSP_STYLE_SRC`, `CSP_SCRIPT_SRC`

**Description**: 
The application utilizes `django-csp` to implement a Content Security Policy. However, both `CSP_STYLE_SRC` and `CSP_SCRIPT_SRC` contain the `'unsafe-inline'` directive. The developer notes indicate this is for Chart.js tooltips and dynamic template styles. 

**Exploitation Scenario**: 
If an attacker finds a Cross-Site Scripting (XSS) vulnerability in the application (e.g., through unescaped user input), the CSP will not prevent the malicious script from executing because `'unsafe-inline'` is permitted.

**Business Impact**: 
An attacker could execute arbitrary JavaScript in the context of an authenticated staff user's session, potentially exfiltrating sensitive data, session cookies, or performing unauthorized actions in the operations portal.

**Recommended Fix**: 
Refactor the frontend to remove inline scripts and styles. Move scripts to external `.js` files or utilize CSP nonces (via `django-csp`'s nonce features) for required inline scripts. Once remediated, remove `'unsafe-inline'` from both directives.

**OWASP Mapping**: A05:2021-Security Misconfiguration
**CWE Mapping**: CWE-358: Improperly Implemented Security Check for Standard

---

## 4. Potential Findings

### 4.1 Unverified Proxy SSL Header Trust
**Severity**: Medium
**Confidence**: Potential
**Affected Files**: `ecofleet/settings.py`
**Affected Configuration**: `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`

**Description**: 
The application trusts the `X-Forwarded-Proto` header to determine if a request was made over HTTPS. This is standard for applications behind a reverse proxy (like Nginx). However, if the reverse proxy is not configured to strip this header from incoming external requests, an attacker can spoof the header.

**Exploitation Scenario**: 
An attacker connects via HTTP and sends the `X-Forwarded-Proto: https` header. If the proxy passes this through, Django will treat the insecure connection as secure, potentially sending `Secure` cookies over plaintext or bypassing `SECURE_SSL_REDIRECT`.

**Business Impact**: 
Potential interception of sensitive session cookies over plaintext networks.

**Recommended Fix**: 
Ensure the upstream proxy (e.g., Nginx) is explicitly configured to strip and overwrite the `X-Forwarded-Proto` header for all incoming requests.

**OWASP Mapping**: A05:2021-Security Misconfiguration
**CWE Mapping**: CWE-345: Insufficient Verification of Data Authenticity

---

### 4.2 Unbounded Cache Key Generation in Performance Middleware
**Severity**: Low
**Confidence**: Potential
**Affected Files**: `core/middleware.py`
**Affected Configuration**: `PerformanceMiddleware`

**Description**: 
The custom `PerformanceMiddleware` tracks the `slowest_endpoint` by storing `request.path` in the cache. It does not bound or sanitize the length of the requested path before caching it.

**Exploitation Scenario**: 
An attacker could send a massive amount of requests with extremely long, randomized paths (e.g., `/non-existent/A*10000`). While it is a single dictionary entry in `FileBasedCache`, tracking arbitrary unvalidated paths can pollute the metrics and use unnecessary memory/disk space.

**Business Impact**: 
Minor impact. Could skew performance metrics or cause slight disk bloat in the cache directory.

**Recommended Fix**: 
Truncate the `request.path` to a reasonable length (e.g., 255 characters) before storing it in the cache metrics.

**OWASP Mapping**: A03:2021-Injection
**CWE Mapping**: CWE-400: Uncontrolled Resource Consumption

---

## 5. Hardening Recommendations

1. **CSP Nonces**: Implement a nonce-based CSP using `request.csp_nonce` provided by `django-csp` to safely allow necessary inline scripts (like Chart.js initialization) while blocking malicious ones.
2. **Environment Variable Validation**: Currently, `DJANGO_ALLOWED_HOSTS` defaults to `127.0.0.1,localhost` if missing. In production, ensure the deployment process strictly validates the presence of critical `.env` variables before starting the application server.
3. **Sentry PII Scrubbing**: Ensure `send_default_pii=False` remains active, and consider adding server-side scrubbing rules in Sentry for any accidentally logged sensitive IDs (like Aadhar/PAN) that might be parsed from the Workbooks.
4. **Log Rotation Limits**: The `TimedRotatingFileHandler` is set to keep 30 days of logs. Ensure the underlying disk has sufficient capacity, or compress older logs, as file processing can generate large volumes of logs quickly.

## 6. Overall Infrastructure Security Rating (0–10)
**Rating: 8/10 (Very Good)**

**Justification**: The infrastructure utilizes secure defaults correctly for production, including HSTS, secure cookies, strict upload limits, and robust brute-force protection. The primary deduction (-2 points) is due to the weakened Content Security Policy (`'unsafe-inline'`), which leaves the application vulnerable to XSS if an injection flaw is found in the views or templates in later audit phases.
