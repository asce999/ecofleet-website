# 02 Authentication Audit

## 1. Executive Summary
This document provides the findings from the Phase 2 white-box security audit, focusing exclusively on the Authentication System of the EcoFleetExpress application. The assessment analyzed login workflows, session management, password security, brute-force protection, and identity handling.

The authentication system leverages Django's robust built-in mechanisms and successfully implements brute-force protection via `django-axes`. However, there are significant weaknesses regarding session lifecycle management (14-day persistent sessions) and missing authentication on the observability endpoint, alongside a likely omission of brute-force protection on the Django admin interface.

## 2. Authentication Architecture
- **Identity Provider**: Django's built-in `auth` module (`django.contrib.auth.models.User`).
- **Authentication Backend**: `django.contrib.auth.backends.ModelBackend` for credential validation, paired with `axes.backends.AxesStandaloneBackend` for lockout enforcement.
- **Session Management**: Django's default database-backed session engine.
- **Brute Force Protection**: `django-axes` package, configured to lock out IP addresses and usernames after 5 failed attempts for 1 hour.
- **Password Hashing**: Django's default PBKDF2 with SHA256.

## 3. Authentication Flow
1. Users attempt access at `/portal/login/`.
2. The `portal_login` view processes credentials using Django's `AuthenticationForm`, which invokes `authenticate()`.
3. `AxesStandaloneBackend` monitors the attempt. Failed attempts trigger `user_login_failed` and increment the axes counter.
4. If authentication succeeds, the view further verifies that `user.is_staff == True`. 
5. Non-staff users are rejected with an error message (and a security log is written).
6. Staff users are logged in via `auth_login()`, which rotates the session key (preventing session fixation) and fires the `user_logged_in` signal.
7. `django-axes` catches the `user_logged_in` signal and clears previous failures (due to `AXES_RESET_ON_SUCCESS = True`).
8. The user receives a session cookie and is redirected to their intended destination via a safe `next` parameter validation.

## 4. Authentication Strengths
- **Secure Password Policies**: `AUTH_PASSWORD_VALIDATORS` enforces similarity checks, minimum length, common password blocking, and numeric-only blocking.
- **Session Fixation Protection**: Standard Django `auth_login()` is used, which correctly rotates the session identifier upon login.
- **Open Redirect Mitigation**: The login view safely handles the `next` parameter by validating it against `ALLOWED_HOSTS` using `url_has_allowed_host_and_scheme`.
- **Brute Force Protection**: `django-axes` is active and configured correctly for the employee portal, mitigating credential stuffing and dictionary attacks.

## 5. Confirmed Findings

### 5.1 Inadequate Session Expiration for Sensitive Portal
**Severity**: Medium
**Confidence**: Confirmed

**Evidence**:
- **File**: `ecofleet/settings.py` (Missing `SESSION_COOKIE_AGE` and `SESSION_EXPIRE_AT_BROWSER_CLOSE`).
- **Why**: By omitting session duration settings, Django falls back to a 14-day persistent session (`SESSION_COOKIE_AGE = 1209600`).

**Description**:
The application does not enforce a strict session expiration policy or an idle timeout. Sessions remain valid for 14 days and persist even after the user closes their browser.

**Attack Preconditions**:
An attacker needs physical or logical access to a user's workstation where a session was left active, or the ability to steal a stale session cookie from an unmanaged device.

**Exploitation Scenario**:
An employee logs into the portal on a shared or untrusted computer, closes the browser without explicitly logging out, and leaves. An attacker later opens the browser on the same machine, navigates to the portal, and accesses the application using the still-valid 14-day persistent session.

**Existing Mitigations**:
None. Sessions must be manually terminated via the logout button.

**Business Impact**:
Unauthorized access to sensitive payroll, attendance, and operational data.

**Recommended Fix**:
Configure `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` to terminate sessions when the browser closes, and reduce `SESSION_COOKIE_AGE` to a shorter timeframe (e.g., 28800 seconds / 8 hours). Implement an absolute or idle timeout mechanism.

**False Positive Considerations**:
None. The fallback to the 14-day default is standard Django behavior when explicitly undefined.

**OWASP Mapping**: A04:2021-Insecure Design (Session Management)
**CWE Mapping**: CWE-613: Insufficient Session Expiration

---

### 5.2 Missing Authentication on Health Check Endpoint
**Severity**: Low
**Confidence**: Confirmed

**Evidence**:
- **File**: `core/views/observability.py`
- **Function**: `health_check(request)`
- **Relevant code path**: The function is exposed at `/health/` (via `core/urls.py`) without the `@staff_required` decorator.
- **Why**: Any anonymous visitor can access this view and extract the JSON response.

**Description**:
The `health_check` endpoint leaks internal application state. It confirms the status of the database connection, the existence of static/media directories, and whether an `AttendanceWorkbook` is currently active.

**Attack Preconditions**:
Network access to the `/health/` endpoint.

**Exploitation Scenario**:
An attacker continuously polls the `/health/` endpoint to map out deployment cycles, database downtime, or to determine exactly when the organization uploads their monthly `AttendanceWorkbook`.

**Existing Mitigations**:
The endpoint does not disclose PII, credentials, or deep technical stack traces.

**Business Impact**:
Minor information disclosure that could assist an attacker in timing subsequent attacks or understanding internal operational rhythms.

**Recommended Fix**:
Require a secret token in the request headers (for automated monitoring tools) or enforce `@staff_required` if it's only meant for manual employee checks.

**False Positive Considerations**:
The endpoint might intentionally be public for an external uptime monitor (like Pingdom). If so, it should still be protected by an API key.

**OWASP Mapping**: A01:2021-Broken Access Control
**CWE Mapping**: CWE-306: Missing Authentication for Critical Function

---

## 6. Likely Findings

### 6.1 Django Admin Interface Lacks Brute Force Protection
**Severity**: Medium
**Confidence**: Likely

**Evidence**:
- **File**: `ecofleet/settings.py`
- **Configuration**: `AXES_ENABLE_ADMIN = False` (with comment: `# don't protect /efe-internal-2026/ separately`)
- **Why**: Disabling this setting in `django-axes` instructs the library to bypass its specific administrative login protections.

**Description**:
The application relies on `django-axes` to protect against brute-force attacks. However, the configuration explicitly disables this protection for the Django Admin panel (`/efe-internal-2026/`). While `AxesStandaloneBackend` hooks into all `authenticate()` calls, setting `AXES_ENABLE_ADMIN = False` can prevent axes from catching admin-specific login signals or overriding the admin login view, leaving it exposed.

**Attack Preconditions**:
An attacker must discover the non-standard admin URL (`/efe-internal-2026/`).

**Exploitation Scenario**:
An attacker discovers the admin URL and launches a high-volume credential stuffing or brute-force attack against the `User` models containing `is_superuser=True` or `is_staff=True`. Since axes is disabled for the admin interface, the attacker will not be locked out.

**Existing Mitigations**:
The admin URL is obfuscated (`/efe-internal-2026/`), providing minor security-through-obscurity.

**Business Impact**:
Complete system compromise if an attacker successfully guesses a high-privileged administrator's password.

**Recommended Fix**:
Remove `AXES_ENABLE_ADMIN = False` (or set it to `True`) so that `django-axes` natively protects the Django admin portal in addition to the custom employee portal.

**False Positive Considerations**:
Because `AxesStandaloneBackend` is in `AUTHENTICATION_BACKENDS`, some versions of axes might still increment failure counts globally for any `authenticate()` call. However, setting the admin flag to False prevents the proper rendering of the lockout response in the admin interface, leading to unpredictable behavior or bypasses.

**OWASP Mapping**: A07:2021-Identification and Authentication Failures
**CWE Mapping**: CWE-307: Improper Restriction of Excessive Authentication Attempts

---

## 7. Potential Findings
(None)

## 8. Hardening Recommendations
1. **Enforce Idle Timeouts**: Beyond setting `SESSION_COOKIE_AGE`, implement middleware to track user inactivity and log them out after 15-30 minutes of idle time.
2. **Implement Multi-Factor Authentication (MFA)**: Given the sensitivity of payroll and operations data, require MFA (e.g., TOTP) for all staff accounts.
3. **Audit Inactive Accounts**: Regularly review the `User` table to ensure that former employees have `is_active=False` and that their sessions are strictly invalidated upon termination.

## 9. Authentication Security Score (0–10)
**Score: 7/10**
The core authentication logic leverages proven framework defaults safely. However, the lack of session expiration controls and the likely omission of admin brute-force protection reduce the score.

## 10. Overall Risk Rating
**Medium**
The risk is constrained by strong password policies, secure cookies, and primary portal brute-force protection. The session expiration flaw and potential admin brute-force exposure represent the most viable attack paths.

## 11. Authentication Maturity Assessment
**Level: Defined (Level 2)**
The authentication mechanisms are explicitly defined and utilize standard, secure framework components. Moving to a "Managed" or "Optimized" maturity level requires strict session lifecycle enforcement, comprehensive brute-force coverage across all entry points, and the introduction of Multi-Factor Authentication (MFA).
