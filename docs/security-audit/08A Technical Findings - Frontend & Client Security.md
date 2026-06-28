# Phase 8A: Frontend & Client Security (Technical Findings)

**Audit Objective:** Analyze client-side components for rendering flaws, input sanitization failures, trust assumptions, insecure storage, and bypasses of client-side validation logic.
**Target Surface:** Django Templates (`core/templates/*`), Client-Side JavaScript, AJAX Handlers, and Browser Security Policies.

---

### FC-001: DOM XSS via Unescaped Column Headers in Dynamic DOM Updates
**Severity:** Critical
**Component:** `templates/core/portal/ftl_form.html`, `templates/core/portal/btpl_form.html`
**Vulnerability Type:** DOM-based Cross-Site Scripting (XSS)

**Technical Evidence:**
The frontend JavaScript responsible for rendering FTL and BTPL workbook data iteratively parses JSON responses from the backend (`?action=preview`) to construct HTML. While the cell contents themselves are properly escaped using the `escHtml()` helper function, the column headers derived from `p.columns` are concatenated into the HTML string *without* escaping:

```javascript
// Excerpt from ftl_form.html (Mobile Card Rendering)
let summaryDetails = [];
row.cells.forEach((cell, idx) => {
  const val = (cell || '').trim();
  if (val !== '' && val !== '0' && p.columns[idx] && !p.columns[idx].toLowerCase().includes('lr number')) {
    // VULNERABILITY: p.columns[idx] is unescaped
    summaryDetails.push(`<span><strong>${p.columns[idx]}:</strong> ${escHtml(val)}</span>`);
  }
});
```
This HTML string is subsequently executed via `mobdiv.innerHTML = mobHtml`. Because `p.columns` is extracted directly from the first row of the active Excel workbook (via `ftl_logic.get_ftl_page_data`), an attacker can simply modify a column header in the Excel file to contain an XSS payload (e.g., `<img src=x onerror=alert(1)>`). This payload will execute in the browser context of any authorized portal user viewing the table when it degrades to the mobile view layout.

---

### FC-002: Client-Side Trust (Unvalidated `row_num` DOM State)
**Severity:** High
**Component:** Client-to-Server Row Operations (`ftl_form.html`, `btpl_form.html`, `pendency_form.html`)
**Vulnerability Type:** Improper Trust in Client State (Bypass of Client Validation)

**Technical Evidence:**
The web application architecture relies heavily on the client to dictate the destination of its write operations via a hidden DOM input:
```html
<input type="hidden" name="row_num" id="fld_row_num" value="{{ next_row }}" />
```
During a normal flow, the frontend queries the API for `?action=next_row` to append data, or `?action=get_row` to edit. The JavaScript dynamically patches the `fld_row_num` hidden input value. However, the client completely trusts this DOM state during the POST operation (`action=save`). 

By using browser Developer Tools or a proxy (e.g., Burp Suite) to intercept and alter the `row_num` field, an attacker can trivially command the backend to overwrite arbitrary rows (e.g., modifying `row_num: 1` to destroy headers, or modifying historical records). This is a frontend architectural flaw (client-trust) that acts as the primary vector for the backend Arbitrary Row Overwrite logic flaw (BL-004).

---

### FC-003: Weakened Content Security Policy (`unsafe-inline`)
**Severity:** Medium
**Component:** `ecofleet/settings.py` (CSP Configuration)
**Vulnerability Type:** Security Misconfiguration

**Technical Evidence:**
The application correctly implements the `django-csp` middleware, but its `script-src` and `style-src` directives are weakened by the inclusion of the `'unsafe-inline'` keyword:

```python
# Excerpt from settings.py
CSP_STYLE_SRC = ("'self'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'", "https://cdn.jsdelivr.net", "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js", "'unsafe-inline'")
```
While a developer comment notes that this is necessary for Chart.js tooltips and dynamic template styles, the presence of `'unsafe-inline'` completely nullifies the CSP's ability to prevent the execution of malicious scripts injected into the DOM (such as those introduced via FC-001). 

---

### FC-004: Missing Subresource Integrity (SRI) on External CDN Assets
**Severity:** Low
**Component:** `templates/core/portal/login.html`, `templates/core/portal/operations_center.html`, `settings.py`
**Vulnerability Type:** Missing Defense-in-Depth

**Technical Evidence:**
Critical frontend dependencies are loaded directly from unauthenticated CDNs (`cdn.jsdelivr.net`) without cryptographic verification (SRI hashes). 
Examples include:
*   `login.html` (Line 27): `@tabler/icons-webfont@3.24.0` (A `TODO(SECURITY)` comment explicitly acknowledges this missing control).
*   `operations_center.html` (Line 9): `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`

If the upstream CDN is compromised or subject to DNS spoofing, the application has no mechanism to reject modified scripts or stylesheets.

---
*Note: Cross-Site Request Forgery (CSRF) protections were reviewed and found to be robustly implemented via Django's `CsrfViewMiddleware`. Standard secure headers (`X-Frame-Options`, `X-Content-Type-Options`) are also adequately configured in the application settings.*
