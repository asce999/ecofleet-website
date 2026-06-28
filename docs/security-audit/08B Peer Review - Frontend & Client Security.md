# Phase 8B: Frontend & Client Security Peer Review

## FC-001: DOM XSS via Unescaped Column Headers in Dynamic DOM Updates

---

## Decision
Accept with Changes

---

## Confidence Review
**Confirmed**
The code analysis is accurate. `p.columns[idx]` is directly concatenated into a string that is assigned to `innerHTML` without HTML escaping, unlike the cell values which pass through `escHtml()`.

---

## Severity Review
**Critical**
The finding correctly identifies this as a Critical vulnerability because it enables Stored/DOM XSS against any user viewing the page. However, the original report missed a crucial nuance regarding execution context (detailed in Browser Compatibility).

---

## Business Criticality Review
**Business Critical**
Exploitation allows full session takeover of operations staff or administrators, potentially granting access to sensitive financial data and system controls.

---

## Reviewer Confidence
**Very High**
The vulnerable code pattern (`element.innerHTML = ... + unescaped_variable + ...`) is a textbook DOM XSS vulnerability. 

---

## Evidence Review
**Strong**
The exact line of code in `ftl_form.html` and `btpl_form.html` is cited. The data flow from the backend JSON response to the `innerHTML` assignment is clear and undeniable.

---

## Browser Compatibility Review
The original report claims an attacker could use `<script>alert(1)</script>`. This is technically incorrect according to the HTML5 specification. Modern browsers (Chrome, Firefox, Safari, Edge) explicitly **do not** execute `<script>` tags inserted via `innerHTML`. 
To achieve execution, the attacker must use inline event handlers (e.g., `<img src="x" onerror="alert(1)">`) or autofocus events (e.g., `<input autofocus onfocus="alert(1)">`). Since the CSP allows `'unsafe-inline'`, this payload will execute across all modern browsers.

---

## User Interaction Review
**Minimal**
The victim only needs to navigate to the FTL or BTPL views and resize their browser window (or view the page on a mobile device) to trigger the `isSummary` logic that generates the `mobHtml`. 

---

## Assumptions
- The backend `format_cell` does not strip HTML characters from the Excel headers. (Verified: it only converts to string).
- The CSP `'unsafe-inline'` rule applies to the injection context.

---

## Counter Evidence
None.

---

## Missing Evidence
The report should explicitly state that the payload must rely on event handlers due to `innerHTML` execution constraints, rather than `<script>` tags.

---

## Reviewer Notes
"Excellent catch on the asymmetric escaping (escaping cells but missing the headers). However, update your exploit payload. When you inject into `innerHTML`, `<script>` tags are dead on arrival per the HTML5 spec. You must use `<img src=x onerror=...>` or similar event handlers. Luckily for the attacker, your FC-003 finding confirms that `'unsafe-inline'` is permitted, making event handler injection viable."

---

## Final Decision
**Accept with Changes** - Update the exploit scenario to specify the use of event handlers instead of `<script>` tags.

---
---

## FC-002: Client-Side Trust (Unvalidated `row_num` DOM State)

---

## Decision
Merge

---

## Confidence Review
**Confirmed**
The frontend indeed passes a user-modifiable hidden input (`row_num`) directly to the backend to determine which row to overwrite.

---

## Severity Review
**High**
Allows arbitrary data corruption.

---

## Business Criticality Review
**Mission Critical**
Data integrity of the primary storage mechanism (Excel workbooks) can be completely compromised.

---

## Reviewer Confidence
**High**
The evidence is clear in the templates and the AJAX requests. 

---

## Evidence Review
**Strong**
The exact HTML element `<input type="hidden" name="row_num" id="fld_row_num">` and its usage in the fetch API call are well documented.

---

## Browser Compatibility Review
Affects all browsers universally, as it is an architectural flaw in the client-server interaction model, not a browser-specific quirk.

---

## User Interaction Review
**None**
An attacker can exploit this via an interception proxy or the browser console without any interaction from a victim user.

---

## Assumptions
- The backend blindly trusts the `row_num` passed in the POST body. (Verified in Phase 7A - BL-004).

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"This is a solid finding that perfectly traces the source of the business logic flaw found in Phase 7A (BL-004). However, because this is fundamentally a backend authorization and state management failure, it should be merged with BL-004 rather than standing as an independent frontend vulnerability. The frontend is simply the mechanism of delivery for a backend vulnerability."

---

## Final Decision
**Merge** - Merge into Phase 7A's BL-004 (Arbitrary Row Overwrite). It serves as the precise client-side evidence for how the business logic flaw is exploited.

---
---

## FC-003: Weakened Content Security Policy (`unsafe-inline`)

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The configuration is present in the `settings.py` file.

---

## Severity Review
**Medium**
It is a defense-in-depth failure. It does not cause a vulnerability on its own, but it removes a primary mitigation layer that would otherwise neutralize FC-001.

---

## Business Criticality Review
**Important**
Renders modern client-side attack mitigations ineffective.

---

## Reviewer Confidence
**Very High**
The CSP headers are explicit and incontrovertible.

---

## Evidence Review
**Strong**
Direct code snippet from `settings.py` showing `'unsafe-inline'` in both script and style sources.

---

## Browser Compatibility Review
All modern browsers respect CSP headers. The weakening affects all users equally.

---

## User Interaction Review
**None**
The policy applies globally to all application users.

---

## Assumptions
None.

---

## Counter Evidence
The developer comment notes that `'unsafe-inline'` is required for `Chart.js` tooltips and dynamic template styles, indicating it is an accepted operational necessity, not an accidental misconfiguration.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Spot on. The inclusion of the developer's comment acknowledging the risk shows good attention to detail. This finding is technically sound and properly contextualizes why FC-001 is exploitable. No changes needed."

---

## Final Decision
**Accept**

---
---

## FC-004: Missing Subresource Integrity (SRI) on External CDN Assets

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The HTML templates load external resources via `<script>` and `<link>` tags without the `integrity` attribute.

---

## Severity Review
**Low**
Exploitation requires compromising a major CDN or performing advanced MITM attacks against encrypted traffic.

---

## Business Criticality Review
**Minor**
While standard practice, the real-world risk is extremely low compared to the other findings.

---

## Reviewer Confidence
**Very High**
The missing attributes are clear in the source code.

---

## Evidence Review
**Strong**
Specific files (`login.html`, `operations_center.html`) and line numbers are cited.

---

## Browser Compatibility Review
All modern browsers support SRI verification. 

---

## User Interaction Review
**None**
If the CDN is compromised, all users requesting the resource are automatically affected.

---

## Assumptions
- The CDN (`cdn.jsdelivr.net`) is considered a third-party risk boundary.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"A standard, automated-scanner-style finding, but technically correct and worth documenting as a defense-in-depth measure. Good inclusion of the `TODO(SECURITY)` comment which proves the developers are already aware of the technical debt."

---

## Final Decision
**Accept**

---
---

# Review Metrics

## Accepted Findings
2 (FC-003, FC-004)

---

## Modified Findings
1 (FC-001)

---

## Rejected Findings
0

---

## Merged Findings
1 (FC-002 -> BL-004)

---

## Confidence Distribution
- Confirmed: 4
- Likely: 0
- Potential: 0

---

## Severity Distribution
- Critical: 1
- High: 1
- Medium: 1
- Low: 1
- Informational: 0

---

## Business Criticality Distribution
- Mission Critical: 1
- Business Critical: 1
- Important: 1
- Minor: 1

---

## Audit Quality Score
**9/10**
The audit accurately identified high-impact vulnerabilities (DOM XSS and Client-Side State Manipulation). The evidence was precise, and the cross-phase correlation with backend business logic flaws was excellent. The only deduction is for the minor technical inaccuracy regarding `<script>` execution inside `innerHTML` assignments, which was corrected in this review.

---

## Coverage Assessment
- **Coverage %:** ~95%
- **Blind Spots:** Single Page Application (SPA) state transitions were not fully modeled, though the application relies mostly on traditional routing with specific AJAX islands, minimizing this risk.
- **Remaining Risks:** Highly convoluted client-side interactions in edge cases (e.g., nested modal forms) might harbor undiscovered state manipulation bugs.

---

## Reviewer Recommendations
- **Browser behaviour:** When reporting XSS vulnerabilities involving `innerHTML` or `outerHTML`, always specify the use of event handlers (like `<img onerror>`) or autofocus inputs, as modern HTML5 parsing rules prevent the execution of injected `<script>` blocks.
- **Cross-phase reasoning:** Continue linking frontend state manipulation bugs to their backend impact. However, classify them primarily as backend authorization failures rather than independent frontend bugs to reduce duplicate reporting in the final enterprise report.
