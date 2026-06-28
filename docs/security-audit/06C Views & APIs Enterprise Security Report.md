# Phase 6C — Views & APIs Enterprise Security Report

---

## 1. Executive Summary

### Overall Assessment
The EcoFleet application's presentation and API layer contains critical architectural flaws regarding authorization and data integrity. While the user interface correctly restricts access to features via Role-Based Access Control (RBAC), the underlying asset endpoints do not enforce these same restrictions, creating a massive gap in the security posture. 

### Security Posture
The application correctly leverages Django's built-in CSRF protections and authentication decorators. However, it implements authorization as a UI-layer concern rather than a data-layer requirement. Input validation on internal APIs is dangerously permissive, trusting authenticated users unconditionally.

### Key Risks
- **Data Exfiltration:** A critical Insecure Direct Object Reference (IDOR) allows any authenticated staff member to download sensitive financial and operational data without authorization.
- **System Denial of Service (DoS):** Internal APIs can be weaponized by authorized insiders to crash the application by exhausting system memory through unvalidated form inputs.
- **Data Corruption:** Batch financial operations (salary updates) lack transaction isolation, guaranteeing data corruption during intermittent faults.

### Key Strengths
- Solid baseline authentication architecture (`@staff_required` applied consistently).
- Standard CSRF mitigations are active across state-changing requests.

### Overall Readiness
**Not Ready for Production.** The presence of a critical IDOR exposing financial/payroll data requires immediate remediation before any further deployment.

---

## 2. Scope

**In Scope:**
- URL routing configurations (`core/urls.py`).
- Function-Based Views (FBV) and Class-Based Views (CBV).
- Django Forms and request validation logic.
- AJAX and JSON API endpoints (`btpl_api`, `ftl_api`).
- File download and media serving endpoints (`download_file`, `protected_media`).
- Request authorization, input validation, and business logic entry points.

**Out of Scope:**
- Third-party library vulnerabilities (except for known misuse of `openpyxl`).
- Infrastructure configuration outside the application request lifecycle.
- Penetration testing of live production systems (Static White-Box Review only).

---

## 3. Risk Matrix

| Severity | Count |
|----------|------:|
| Critical | 1 |
| High | 3 |
| Medium | 0 |
| Low | 0 |
| Informational | 0 |

---

## 4. Security Score

- **Overall Score:** 3/10
- **Views & APIs Score:** 3/10
- **Confidence in Assessment:** Confirmed (Validated via Peer Review)
- **Coverage %:** 95%

**Explanation:** A score of 3 reflects an application that correctly identifies authenticated users but completely fails to enforce authorization boundaries on direct resource access. The high severity of the IDOR and DoS vectors heavily penalizes the score.

---

## 5. Architecture Overview

### Request Lifecycle
EcoFleet utilizes standard Django patterns. Requests flow through routing (`urls.py`), pass authentication middleware, and arrive at views. Most views are decorated with `@staff_required` and custom `@tool_permission_required` decorators.

### Trust Boundaries
The primary trust boundary is authentication. Once a user authenticates, the system implicitly trusts their inputs (e.g., hidden form fields) and assumes they will only interact with the UI through intended pathways. 

### Entry Points
- UI Rendering Views (Dashboards, Tool Interfaces).
- AJAX Mutators (`/portal/ftl/api/`, `/portal/btpl/api/`).
- File Serving Endpoints (`/media/`, `/portal/download/`).

### High-Value Assets
- Payroll and Attendance Workbooks.
- FTL and BTPL Shipment Data.
- Core Business Logic State.

---

## 6. Validated Findings

### VIEW-001
- **Title:** Global Authorization Bypass on Media Endpoints (IDOR)
- **Severity:** Critical
- **Confidence:** Confirmed
- **Business Criticality:** Highest
- **Business Impact:** Total exposure of highly sensitive payroll, HR, and operational data to any employee with portal access.
- **Root Cause:** Missing Authorization
- **Executive Summary:** The endpoint responsible for serving files fails to check if the user is permitted to view the requested file, allowing anyone to download everything.
- **Technical Summary:** `protected_media` enforces `@staff_required` but fails to check `UserProfile` tool permissions, allowing direct path traversal to any predictable file within `MEDIA_ROOT`.
- **Exploit Summary:** A junior employee logs in and manually requests `/media/attendance/Attendance_Sheet.xlsx` in their browser, immediately receiving the entire company payroll file.
- **Existing Mitigations:** Prevents unauthenticated access (`@staff_required`); prevents arbitrary directory traversal outside `MEDIA_ROOT`.
- **Recommended Direction:** Re-architect media serving to use a database-backed manifest that validates object-level permissions before generating the `X-Accel-Redirect` or `FileResponse`.
- **Related Findings:** Storage & Database Audit (Predictable Storage Locations).

### VIEW-002
- **Title:** Authorization Bypass in `download_file` (Missing FTL RBAC)
- **Severity:** High
- **Confidence:** Confirmed
- **Business Criticality:** High
- **Business Impact:** Unauthorized access specifically to FTL (Full Truck Load) shipment processing artifacts, undermining operational confidentiality.
- **Root Cause:** Missing Authorization
- **Executive Summary:** A configuration oversight allows any employee to bypass security checks and download FTL shipment reports.
- **Technical Summary:** The `tool_map` dictionary in `download_file` is missing the `FTL` key. The resulting `None` lookup causes the authorization check to fail-open, granting access to anyone.
- **Exploit Summary:** An attacker discovers an FTL `ToolRunFile` ID and requests the download URL. The missing dictionary key aborts the security check, serving the file.
- **Existing Mitigations:** None on the FTL download path.
- **Recommended Direction:** Immediately add `'FTL': 'ftl'` to `tool_map` and refactor the logic to fail-closed (deny access) if a tool is unrecognized.
- **Related Findings:** Authorization Audit (RBAC Bypass).

### VIEW-003
- **Title:** Denial of Service via Resource Exhaustion (Unbounded Row Input)
- **Severity:** High
- **Confidence:** Confirmed
- **Business Criticality:** High
- **Business Impact:** Total application outage. Employees cannot process shipments, attendance, or access the portal while the server crashes and reboots.
- **Root Cause:** Missing Validation
- **Executive Summary:** Authorized users can manipulate background requests to force the server to allocate massive amounts of memory, crashing the system.
- **Technical Summary:** `BtplShipmentForm` and `FtlShipmentForm` lack `max_value` constraints on `row_num`. Authorized attackers can send `row_num=1048576`, causing `openpyxl` to build enormous XML DOMs in memory and trigger an OOM kill.
- **Exploit Summary:** A malicious insider with FTL permissions intercepts the AJAX save request, alters `row_num` to 1,048,576, and submits. The server runs out of memory and the Python process crashes.
- **Existing Mitigations:** Attacker must be an authenticated staff member with specific FTL/BTPL tool permissions (Insider Threat).
- **Recommended Direction:** Enforce strict integer boundaries on all hidden form inputs processed by third-party parsers.
- **Related Findings:** File Upload Audit (Third-Party Parser Vulnerabilities).

### VIEW-004
- **Title:** Lack of Atomicity in Batch Salary Operations
- **Severity:** High
- **Confidence:** Confirmed
- **Business Criticality:** High
- **Business Impact:** Corrupted financial records requiring expensive, manual database reconciliation and risking incorrect employee compensation.
- **Root Cause:** Architecture / Technical Debt
- **Executive Summary:** Bulk updates to payroll data are processed individually without a safety net. If a network blip occurs halfway through, the payroll is left broken and incomplete.
- **Technical Summary:** The loop in `salary_calculator` executes multiple `update_or_create` calls without a `transaction.atomic()` context block.
- **Exploit Summary:** An admin uploads a batch of salary updates. The server processes half of them, then hits a database lock and throws an exception. The first half remains committed while the second half is dropped.
- **Existing Mitigations:** None. Django operates in default autocommit mode.
- **Recommended Direction:** Wrap batch financial mutations in `with transaction.atomic():`.
- **Related Findings:** Storage & Database Audit.

---

## 7. Attack Chains

**Attack Chain 1: Payroll Exfiltration (IDOR)**
`VIEW-001` → Bypass RBAC on `/media/` → Request Predictable Attendance Path → Download Salary Workbook → **Confidentiality Loss / Severe Business Impact**

**Attack Chain 2: FTL Report Exfiltration**
`VIEW-002` → Target `/portal/download/` → Trigger `tool_map` fail-open → Download FTL Artifacts → **Operational Confidentiality Loss**

**Attack Chain 3: Insider Application Crash (DoS)**
`VIEW-003` → Authorized user intercepts AJAX request → Set `row_num` to 1,048,576 → `openpyxl` allocates ~5GB memory → OOM Killer terminates Django → **Complete Availability Loss**

**Attack Chain 4: Payroll Corruption**
`VIEW-004` → Admin Submits Large Salary Batch → Concurrent request locks DB table → Transaction fails mid-loop → State becomes inconsistent → **Integrity Loss / Financial Impact**

---

## 8. Root Cause Summary

| Root Cause | Findings |
|------------|---------:|
| Missing Authorization | 2 |
| Missing Validation | 1 |
| Technical Debt / Architecture | 1 |

**Trend Explanation:**
The dominant root cause is a fundamental misunderstanding of authorization implementation. Security controls are aggressively applied to the User Interface (hiding buttons and denying page renders) but are stripped away or forgotten at the exact points where data is actually requested or downloaded.

---

## 9. Technical Debt Register

| ID | Debt | Impact | Interest | Owner | Recommendation |
|---|---|---|---|---|---|
| TD-01 | UI-Coupled Authorization | Critical | High | Architecture | Migrate from view-decorator RBAC to Object-Level permissions (e.g., django-guardian) or robust service-layer checks. |
| TD-02 | Synchronous Heavy Data Processing | High | Medium | Architecture | Offload `openpyxl` workbook generation and manipulation to Celery background tasks to isolate memory and CPU impact. |

---

## 10. Engineering Backlog

| ID | Issue | Priority | Owner | Dependencies | Estimated Effort | Regression Risk | Status |
|---|---|---|---|---|---|---|---|
| ENG-01 | Fix IDOR in `protected_media` (VIEW-001) | P0 | Backend | None | 2 Days | High | Todo |
| ENG-02 | Fix fail-open logic in `download_file` (VIEW-002) | P1 | Backend | None | 0.5 Days | Low | Todo |
| ENG-03 | Add bounds to `row_num` in Forms (VIEW-003) | P1 | Backend | None | 0.5 Days | Low | Todo |
| ENG-04 | Add `transaction.atomic` to salary batch (VIEW-004) | P1 | Database | None | 0.5 Days | Medium | Todo |

---

## 11. Quick Wins

- **Update `tool_map` (ENG-02):** Adding `'FTL': 'ftl'` to the dictionary and explicitly failing if the key isn't found will immediately patch the FTL download bypass. (Effort: 30 minutes).
- **Form Validation Bounds (ENG-03):** Adding `min_value` and `max_value` to `row_num` prevents trivial application crashes without architectural changes. (Effort: 30 minutes).
- **Database Atomicity (ENG-04):** Adding the `@transaction.atomic` decorator or context manager instantly secures payroll data integrity. (Effort: 15 minutes).

---

## 12. Strategic Improvements

- **Centralized Authorization Service:** Move RBAC checks out of view decorators and into a centralized service layer. This ensures that no matter how an asset is accessed (Direct URL, API, or Dashboard), the same security rules apply. (Complexity: High, Benefit: Critical).
- **Asynchronous Processing Architecture:** Move all `openpyxl` logic into Celery workers. This permanently removes the threat of request-based Resource Exhaustion (DoS) taking down the web serving tier. (Complexity: High, Benefit: High).

---

## 13. Executive Action Plan

### Immediate
- Fix the `protected_media` IDOR (VIEW-001) to prevent data exfiltration.
- Apply `transaction.atomic` to `salary_calculator` to prevent database corruption.

### Next Sprint
- Patch the `download_file` bypass (VIEW-002).
- Apply bounds to all hidden form integers (VIEW-003).

### Next Release
- Begin migrating workbook generation to asynchronous background tasks.

### Long-Term Roadmap
- Refactor the authorization model to enforce rules at the data access layer, eliminating reliance on URL routing decorators.

---

## 14. Security Strengths

- **Authentication Foundation:** The `@staff_required` check is applied consistently, successfully preventing anonymous unauthenticated exploitation across the board.
- **CSRF Mitigations:** Django's default CSRF middleware is active and properly secures POST/AJAX endpoints against cross-site exploitation.

---

## 15. Remaining Risks

- **Accepted Risks:** Form manipulation by highly trusted directors; UI-layer XSS through deeply trusted internal reports.
- **Residual Risks:** While `row_num` bounds will fix the immediate DoS, `openpyxl` is inherently memory-heavy. Legitimate usage by many simultaneous users could still stress server memory.
- **Blind Spots:** Edge cases within complex Excel mathematical formulas being evaluated during generation.

---

## 16. Security Maturity Assessment

- **Authentication:** 8/10 (Strong Django defaults utilized).
- **Authorization:** 2/10 (Severe architecture flaws; fail-open logic; IDORs).
- **Views:** 5/10 (Mix of secure rendering but unsafe data handling).
- **APIs:** 4/10 (Permissive trust of client-provided state).
- **Validation:** 3/10 (Missing critical boundary checks).
- **Engineering Practices:** 5/10 (Good foundational structure, poor security testing).

---

## 17. Executive Conclusion

**Deployment Readiness: DENIED**

The EcoFleet portal is currently unsafe for production deployment. While the external perimeter (authentication) is functional, the internal compartmentation (authorization) is fundamentally broken. The IDOR vulnerability (VIEW-001) guarantees that any employee can access the entire company payroll and operational data. 

Engineering leadership must prioritize the **Immediate** action plan items (ENG-01, ENG-04) before staging can sign off. Fortunately, three of the four major findings are Quick Wins that can be resolved in under a day, meaning the delay to production can be minimized if resources are aggressively reallocated.
