# Phase 9A: Dependencies & Supply Chain Security Audit (Technical Findings)

**Audit Objective:** Identify supply chain and dependency security risks across the application's third-party Python packages, JavaScript libraries, and Content Delivery Networks (CDNs).
**Target Surface:** `requirements.txt`, HTML Templates (CDN links), Package Documentation.

---

### DEP-001: Floating Dependency Version in Third-Party CDN
**Severity:** Medium
**Confidence:** Confirmed
**Business Criticality:** Important

**Affected Dependencies:**
- Package: Chart.js
- Version: Unpinned (Latest)
- Usage: `templates/core/portal/operations_center.html`

**Evidence:**
- File: `templates/core/portal/operations_center.html` (Line 9)
- Configuration: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`

**Technical Description:**
The operations center template requests the Chart.js library from the jsdelivr CDN without specifying a version tag. By default, npm/jsdelivr will serve the latest available version of the package. This is a floating dependency. 

**Business Impact:**
If the maintainers of Chart.js push a backward-incompatible major version, the operations dashboard will break without warning. More critically, if the jsdelivr cache or the npm registry is compromised (supply chain attack) and a malicious update is published to Chart.js, the EcoFleet Express portal will immediately and automatically ingest and execute the malicious payload for all users.

**Root Cause:**
- Dependency Management

**Why this is a Supply Chain Risk:**
- **Package Behaviour:** The CDN resolves the URL to the highest available version dynamically.
- **Operational Behaviour:** The application automatically trusts the upstream provider to serve safe, compatible code on every page load.

**Cross-Phase References:**
- FC-004: Missing Subresource Integrity (SRI) on External CDN Assets (Phase 8A). The lack of version pinning compounds the lack of SRI.

**Counter Argument:**
The dashboard template (`dashboard.html`) correctly pins the version (`chart.js@4.4.1/dist/chart.umd.min.js`). The floating version only exists in the `operations_center.html` template.

**Confidence Review:**
The code evidence directly shows the absence of a version specifier in the URL.

**Exploit Complexity:** High (Requires upstream registry or CDN compromise).
**Detection Difficulty:** Easy

---

### DEP-002: Abandoned Security Dependency (`django-csp`)
**Severity:** Low
**Confidence:** Confirmed
**Business Criticality:** Minor

**Affected Dependencies:**
- Package: django-csp
- Version: 3.7
- Usage: `requirements.txt` / `ecofleet/settings.py`

**Evidence:**
- File: `requirements.txt` (Line 10: `django-csp==3.7`)

**Technical Description:**
The application relies on `django-csp` to manage and inject Content Security Policy (CSP) headers. Version 3.7 is installed, which is the latest version available on PyPI. However, the official Mozilla repository for this package (`mozilla/django-csp`) has been archived and is no longer actively maintained. 

**Business Impact:**
As a security-critical package, relying on an unmaintained library means that if future vulnerabilities are discovered within the library itself, or if future versions of Django introduce breaking changes, no official patches will be provided.

**Root Cause:**
- Supply Chain

**Why this is a Supply Chain Risk:**
- **Package Behaviour:** The package is frozen at version 3.7 and receives no updates.
- **Framework Behaviour:** Future Django upgrades may break compatibility with this middleware.

**Cross-Phase References:**
- FC-003: Weakened Content Security Policy (Phase 8A). The application already misconfigures the output of this package.

**Counter Argument:**
The library is essentially feature-complete for basic CSP header injection and does not process complex user input, making its attack surface extremely small despite being unmaintained.

**Confidence Review:**
Verified via Mozilla's GitHub repository status (Archived).

**Exploit Complexity:** High
**Detection Difficulty:** Easy

---

### DEP-003: Mitigated XML Attack Surface (Informational)
**Severity:** Informational
**Confidence:** Confirmed
**Business Criticality:** Minor

**Affected Dependencies:**
- Package: openpyxl
- Version: 3.1.5
- Auxiliary Package: defusedxml
- Version: 0.7.1
- Usage: `requirements.txt` / Workbook Parsing

**Evidence:**
- File: `requirements.txt` (Line 3: `openpyxl==3.1.5`, Line 9: `defusedxml==0.7.1`)
- Documentation Reference: "To protect against XML-based attacks like quadratic blowup and billion laughs, it is recommended to install the defusedxml library, as openpyxl does not provide these protections by default." (openpyxl Security Documentation)

**Technical Description:**
The application relies heavily on `openpyxl` (via pandas and direct usage) to parse uploaded `.xlsx` files. Excel files are essentially ZIP archives containing XML files. By default, parsing XML can expose the application to XXE (XML External Entity) and XML Bomb (Billion Laughs) attacks. However, the `defusedxml` package is explicitly included in the project's dependencies. `openpyxl` automatically detects `defusedxml` and uses it to parse XML securely.

**Business Impact:**
The inclusion of `defusedxml` successfully neutralizes a severe class of supply chain and parsing vulnerabilities (XXE), securing the file upload workflows.

**Root Cause:**
- Configuration (Secure Default Override)

**Why this is a Supply Chain Risk:**
- **Package Behaviour:** `openpyxl` uses standard library XML parsers which are vulnerable by default unless `defusedxml` is present.
- **Operational Behaviour:** The environment securely overrides dangerous defaults.

**Cross-Phase References:**
- Phase 4: File Upload & Workbook Security Audit. This confirms the safety of the underlying XML parser for workbook uploads.

**Counter Argument:**
This is a secure configuration, not a vulnerability.

**Confidence Review:**
Verified via `requirements.txt` and `openpyxl` official documentation.

**Exploit Complexity:** Very High (Currently Mitigated)
**Detection Difficulty:** Easy
