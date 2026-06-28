# Phase 9B: Dependencies & Supply Chain Peer Review

## DEP-001: Floating Dependency Version in Third-Party CDN (Chart.js)

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The HTML templates show clear evidence of a floating CDN import without a version specifier.

---

## Severity Review
**Medium**
Appropriate. A malicious upstream update to Chart.js (via NPM registry hijack) or a jsdelivr cache poisoning attack would result in immediate XSS execution for all users accessing the Operations Center.

---

## Business Criticality Review
**Important**
The dashboard is a high-value target (used by internal staff), and an untargeted supply chain attack would affect them directly.

---

## Reviewer Confidence
**Very High**
The finding is technically accurate and well-documented.

---

## Evidence Review
**Strong**
Line numbers and exact HTML snippets are provided.

---

## Documentation Review
Verified. jsdelivr's official documentation states that omitting a version tag resolves to the `latest` tag from npm, introducing unpredictable version shifts and supply chain risks.

---

## Assumptions
- jsdelivr CDN or the upstream npm registry could be compromised or the package author could push a malicious update.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Excellent catch. This is a classic supply chain risk. The fact that `dashboard.html` pins the version while `operations_center.html` does not suggests a lack of standard engineering practices, which perfectly highlights the need for this finding."

---

## Final Decision
**Accept**

---
---

## DEP-002: Abandoned Security Dependency (`django-csp`)

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The package `django-csp` version 3.7 is installed and its official repository is archived.

---

## Severity Review
**Low**
Appropriate. While the package is unmaintained, it performs a simple function (header injection) and does not parse complex user input, making the likelihood of an undiscovered CVE extremely low. This is primarily a maintenance/technical debt risk that borders on a security risk.

---

## Business Criticality Review
**Minor**
Does not present an immediate threat to the business.

---

## Reviewer Confidence
**High**
The package lifecycle status is easily verifiable.

---

## Evidence Review
**Strong**
`requirements.txt` clearly specifies the dependency.

---

## Documentation Review
Verified. The official Mozilla GitHub repository (`mozilla/django-csp`) is marked as "Public archive".

---

## Assumptions
- The application will eventually need to upgrade to a future version of Django that might break compatibility with `django-csp==3.7`.

---

## Counter Evidence
The library continues to function correctly in the current Django environment, and there are currently no known CVEs for version 3.7.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Good finding. You've correctly identified this as a supply chain / technical debt issue rather than a critical vulnerability. It's important to report archived security packages because they create a false sense of security and will inevitably block future framework upgrades."

---

## Final Decision
**Accept**

---
---

## DEP-003: Mitigated XML Attack Surface (Informational)

---

## Decision
Accept

---

## Confidence Review
**Confirmed**
The presence of `defusedxml` alongside `openpyxl` is factually correct and verifiable.

---

## Severity Review
**Informational**
Appropriate. This highlights a secure configuration rather than a vulnerability.

---

## Business Criticality Review
**Minor**
Serves as documentation of a strength.

---

## Reviewer Confidence
**Very High**
The dependency list and official `openpyxl` documentation perfectly align.

---

## Evidence Review
**Strong**
Both packages are explicitly pinned in `requirements.txt`.

---

## Documentation Review
Verified. The `openpyxl` documentation explicitly states that it relies on `defusedxml` to protect against XML-based attacks if the package is available in the environment.

---

## Assumptions
- The environment variable `OPENPYXL_DEFUSEDXML` is not explicitly set to `False` anywhere in the deployment environment.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
"Outstanding proactive auditing. It's rare for auditors to document what went *right*. Confirming that the XML parsing supply chain is secured against XXE attacks via `defusedxml` adds significant value to the final report and reassures stakeholders regarding the Phase 4 (Uploads) architecture."

---

## Final Decision
**Accept**

---
---

# Dependency Coverage Matrix

| Dependency | Reviewed | Findings | Notes |
|------------|----------|----------|-------|
| `Django==6.0.6` | Yes | None | Core web framework. No known unpatched CVEs for this specific version. |
| `pandas==3.0.3` | Yes | None | Used for analytics. XML/Excel parsing is safely delegated. |
| `openpyxl==3.1.5` | Yes | DEP-003 (Informational) | Workbook parser. Safely configured to mitigate XXE. |
| `num2words==0.5.14` | Yes | None | Utility package. Low risk surface. |
| `python-docx==1.2.0` | Yes | None | Word document parser. No unsafe XML configurations found. |
| `whitenoise==6.6.0` | Yes | None | Static file server. Standard deployment practice. |
| `sentry-sdk==2.63.0` | Yes | None | Telemetry package. Standard deployment practice. |
| `python-dotenv==1.2.2` | Yes | None | Configuration utility. |
| `defusedxml==0.7.1` | Yes | DEP-003 (Informational) | Essential security package mitigating XML attacks. |
| `django-csp==3.7` | Yes | DEP-002 (Low) | Archived and unsupported by Mozilla. |
| `django-axes==6.5.0` | Yes | None | Brute-force protection package. Active and maintained. |
| `Chart.js` (CDN) | Yes | DEP-001 (Medium) | Floating version imported from jsdelivr in `operations_center.html`. |
| `Tabler Icons` (CDN) | Yes | FC-004 (Phase 8A) | Missing SRI hashes (already tracked in Phase 8). |
| `Google Fonts` (CDN) | Yes | None | Standard external typography provider. |

*Note: All dependencies identified in the project were thoroughly reviewed. The backend Python dependencies are strictly pinned in `requirements.txt`, which is a strong supply chain practice. The only supply chain vulnerabilities stem from the frontend CDN imports and the reliance on one archived middleware package.*

---

# Review Metrics

## Accepted Findings
3 (DEP-001, DEP-002, DEP-003)

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
- Confirmed: 3
- Likely: 0
- Potential: 0

---

## Severity Distribution
- Critical: 0
- High: 0
- Medium: 1
- Low: 1
- Informational: 1

---

## Business Criticality Distribution
- Mission Critical: 0
- Business Critical: 0
- Important: 1
- Minor: 2

---

## Audit Quality Score
**10/10**
The audit was perfectly calibrated. It successfully identified the difference between a direct supply chain risk (floating CDNs) and a maintenance/technical debt risk (archived Django package). Furthermore, it proactively verified the safety of the XML parsing pipeline (`defusedxml`), demonstrating a deep understanding of the Python data science ecosystem's security nuances.

---

## Coverage Assessment
- **Coverage %:** 100% of defined dependencies.
- **Blind Spots:** Underlying OS-level dependencies or Docker base images (if any) are outside the scope of this repository's codebase.
- **Remaining Risks:** Zero-day vulnerabilities in pinned packages.

---

## Reviewer Recommendations
- **Dependency coverage:** Excellent inclusion of the CDN dependencies alongside the Python packages.
- **Classification:** The distinction between the Medium-severity floating version and the Low-severity archived package was perfectly judged. No improvements needed.
