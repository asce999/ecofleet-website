# Graph Report - EcoFleetExpress  (2026-06-28)

## Corpus Check
- 125 files · ~141,186 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1439 nodes · 1915 edges · 92 communities (69 shown, 23 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 99 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4e440c04`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 88|Community 88]]

## God Nodes (most connected - your core abstractions)
1. `Phase 10B: Logging, Monitoring & Auditability Peer Review` - 79 edges
2. `Phase 11B: Deployment & Production Hardening Peer Review` - 79 edges
3. `Phase 8B: Frontend & Client Security Peer Review` - 57 edges
4. `ProviderResult` - 49 edges
5. `Phase 7B — Business Logic Peer Review` - 49 edges
6. `CheckResult` - 43 edges
7. `Phase 9B: Dependencies & Supply Chain Peer Review` - 40 edges
8. `BaseProvider` - 31 edges
9. `ToolRun` - 26 edges
10. `12 Enterprise Software Assurance Report` - 23 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `to_json()`  [INFERRED]
  build_graph.py → core/templatetags/core_extras.py
- `WorkbookUploadForm` --uses--> `SalaryConfig`  [INFERRED]
  core/forms.py → core/models.py
- `CofForm` --uses--> `SalaryConfig`  [INFERRED]
  core/forms.py → core/models.py
- `PendencyForm` --uses--> `SalaryConfig`  [INFERRED]
  core/forms.py → core/models.py
- `MorningForm` --uses--> `SalaryConfig`  [INFERRED]
  core/forms.py → core/models.py

## Import Cycles
- None detected.

## Communities (92 total, 23 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (79): Assumptions, Assumptions, Assumptions, Assumptions, Assumptions, Assumptions, Business Criticality Review, Business Criticality Review (+71 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (79): Assumptions, Assumptions, Assumptions, Assumptions, Assumptions, Assumptions, Business Criticality Review, Business Criticality Review (+71 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (37): BaseCommand, Command, Command, Command, Command, Event log for all meaningful operational and business activities., SystemEvent, ActivityProvider (+29 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (64): Affected Components, Affected Components, Affected Components, Affected Components, Business Criticality, Business Criticality, Business Criticality, Business Criticality (+56 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (57): Assumptions, Assumptions, Assumptions, Assumptions, Browser Compatibility Review, Browser Compatibility Review, Browser Compatibility Review, Browser Compatibility Review (+49 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (48): Affected Components, Affected Components, Affected Components, Affected Components, Confidence, Confidence, Confidence, Confidence (+40 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (49): Assumptions, Assumptions, Assumptions, Assumptions, Business Criticality Review, Business Criticality Review, Business Criticality Review, Business Criticality Review (+41 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (24): Command, CofWorkbookAdmin, PincodeAdmin, ToolRunAdmin, ToolRunFileInline, AttendanceWorkbook, BtplWorkbook, CofWorkbook (+16 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (40): Assumptions, Assumptions, Assumptions, Assumptions, Confidence Review, Confidence Review, Confidence Review, Confidence Review (+32 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (40): Assumptions, Assumptions, Assumptions, Business Criticality Review, Business Criticality Review, Business Criticality Review, Confidence Review, Confidence Review (+32 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (35): 10. Engineering Backlog, 11. Quick Wins, 12. Strategic Improvements, 13. Executive Action Plan, 14. Security Strengths, 15. Remaining Risks, 16. Security Maturity Assessment, 17. Executive Conclusion (+27 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (33): build_new_rows(), clean_delhivery(), find_lr_col(), find_pincode_col(), generate(), load_master(), load_pincode_map(), normalize_lr() (+25 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (34): 10. Engineering Backlog, 11. Finding Traceability Matrix, 12. Quick Wins, 13. Strategic Improvements, 14. Executive Action Plan, 15. Business Logic Strengths, 16. Remaining Risks, 17. Business Logic Maturity Assessment (+26 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (7): CofForm, MorningForm, PendencyForm, PrevMonthUpdateForm, validate_xlsx_upload(), morning_report(), prev_month_update()

### Community 14 - "Community 14"
Cohesion: 0.04
Nodes (47): 10. Activity Explorer, 11. Configuration-Driven Quick Actions, 12. Historical Trends, 13. Future Readiness, 1. Files Modified, 1. Preserve Portal Layout, 2. Architecture Summary, 2. DashboardViewModel (MANDATORY) (+39 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (29): 08C Frontend & Client Security Enterprise Report, 10. Engineering Backlog, 11. Finding Traceability Matrix, 12. Quick Wins, 13. Strategic Improvements, 14. Executive Action Plan, 15. Frontend Security Strengths, 16. Remaining Risks (+21 more)

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (28): 10. Root Cause Summary, 11. Technical Debt Register, 11C Deployment & Production Hardening Enterprise Security Report, 12. Engineering Backlog, 13. Finding Traceability Matrix, 14. Quick Wins, 15. Strategic Improvements, 16. Deployment Strengths (+20 more)

### Community 17 - "Community 17"
Cohesion: 0.14
Nodes (20): WorkbookUploadForm, attendance_sheet(), salary_calculator(), cof_generator(), cof_history(), cof_success(), cof_workbook(), cof_workbook_download() (+12 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (27): 10. Technical Debt Register, 10C Logging, Monitoring & Auditability Enterprise Security Report, 11. Engineering Backlog, 12. Finding Traceability Matrix, 13. Quick Wins, 14. Strategic Improvements, 15. Observability Strengths, 16. Remaining Risks (+19 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (24): 09C Dependencies & Supply Chain Enterprise Security Report, 10. Technical Debt Register, 11. Engineering Backlog, 12. Finding Traceability Matrix, 13. Quick Wins, 14. Strategic Improvements, 15. Dependency Security Strengths, 16. Remaining Risks (+16 more)

### Community 20 - "Community 20"
Cohesion: 0.16
Nodes (22): amount_to_words(), append_data_sheet(), AssetMissing, build_cert_text(), build_word_doc(), COFLockTimeout, create_cof_sheet(), generate_cof() (+14 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (23): 10. Technical Debt Assessment, 11. Consolidated Findings, 12 Enterprise Software Assurance Report, 12. Risk Heatmap, 13. Engineering Backlog, 14. Technical Debt Register, 15. Quick Wins, 16. Strategic Roadmap (+15 more)

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (22): 10. Likely Findings, 11. Potential Findings, 12. Attack Chains, 13. Engineering Backlog, 14. Hardening Recommendations, 15. Storage Security Score (0–10), 16. Overall Risk Rating, 17. Storage Maturity Assessment (+14 more)

### Community 23 - "Community 23"
Cohesion: 0.14
Nodes (20): apply_observations(), _col(), extract_month_label(), _find_col(), generate(), load_delayed(), load_observation_csvs(), _norm_lr() (+12 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (20): 00 Project Understanding, APIs, Architecture, Attack Surface Overview, Authentication Flow, Authorization Flow, Data Flow, Database Overview (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.18
Nodes (13): FtlShipmentForm, FtlWorkbookUploadForm, Returns a file stream for a workbook object, or the fallback template if none ex, Locates the default template for a given tool and copies it to the media directo, WorkbookManager, attendance_download(), ftl_api(), ftl_download() (+5 more)

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (18): 03 Authorization Audit, 10. Hardening Recommendations, 11. Authorization Security Score (0–10), 12. Overall Risk Rating, 13. Authorization Maturity Assessment, 1. Executive Summary, 2. Authorization Architecture, 3. Authorization Flow (+10 more)

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (10): BytesIO, AttendanceWorkbookUploadForm, Meta, SalaryConfigForm, Singleton model to store global payroll rates and settings., SalaryConfig, generate_salary_export(), attendance_settings() (+2 more)

### Community 28 - "Community 28"
Cohesion: 0.21
Nodes (16): add_btpl_shipment(), clear_btpl_row(), evaluate_cell(), find_next_btpl_row(), find_totals_row(), get_btpl_page_data(), get_btpl_preview(), get_btpl_row_values() (+8 more)

### Community 29 - "Community 29"
Cohesion: 0.18
Nodes (11): BtplShipmentForm, BtplWorkbookUploadForm, get_sheet_names(), Returns a list of sheet names from an Excel file, or an empty list if it cannot, btpl_api(), btpl_download(), btpl_settings(), btpl_sheet() (+3 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (15): 02 Authentication Audit, 10. Overall Risk Rating, 11. Authentication Maturity Assessment, 1. Executive Summary, 2. Authentication Architecture, 3. Authentication Flow, 4. Authentication Strengths, 5.1 Inadequate Session Expiration for Sensitive Portal (+7 more)

### Community 31 - "Community 31"
Cohesion: 0.24
Nodes (14): add_ftl_shipment(), clear_ftl_row(), derive_status(), evaluate_cell(), find_next_ftl_row(), find_totals_row(), get_cached_ftl_metrics(), get_column_mapping() (+6 more)

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (13): 1. XML Decompression Bomb (ZIP Bomb) in XLSX Uploads, 1. XML External Entity (XXE) / Billion Laughs Attack via `openpyxl`, 2. Path Traversal / Header Injection via `original_name` in Uploaded Files, 2. Unrestricted File Size leading to OOM (Denial of Service) via CSV Uploads, 3. Formula Injection (CSV / Excel Injection) in Workbook Writes, 4. Data Integrity Loss via Concurrent Workbook Modifications, Confirmed Vulnerabilities, Detailed Findings (+5 more)

### Community 33 - "Community 33"
Cohesion: 0.22
Nodes (9): calculate_salary_data(), get_active_attendance_workbook(), get_attendance_data(), get_days_in_sheet(), get_month_year_from_sheet(), get_working_days(), save_attendance(), EmployeeSalaryOverride (+1 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (12): Accepted Findings, Audit Quality Score, Business Criticality Distribution, Confidence Distribution, Coverage Assessment, Dependency Coverage Matrix, Merged Findings, Modified Findings (+4 more)

### Community 35 - "Community 35"
Cohesion: 0.15
Nodes (12): Accepted Findings, Audit Quality Score, Business Criticality Distribution, Confidence Distribution, Coverage Assessment, Logging Coverage Matrix, Merged Findings, Modified Findings (+4 more)

### Community 36 - "Community 36"
Cohesion: 0.15
Nodes (12): Accepted Findings, Audit Quality Score, Business Criticality Distribution, Confidence Distribution, Coverage Assessment, Merged Findings, Modified Findings, Production Readiness Matrix (+4 more)

### Community 37 - "Community 37"
Cohesion: 0.17
Nodes (15): director_required(), Allow only authenticated staff (employees) into the portal., Enforce tool permissions based on UserProfile., Allow only users with Director role., staff_required(), tool_permission_required(), _get_all_lrs_from_workbook(), pendency_observations() (+7 more)

### Community 38 - "Community 38"
Cohesion: 0.17
Nodes (11): Accepted Findings, Audit Quality Score, Business Criticality Distribution, Confidence Distribution, Coverage Assessment, Merged Findings, Modified Findings, Rejected Findings (+3 more)

### Community 39 - "Community 39"
Cohesion: 0.17
Nodes (11): Accepted Findings, Audit Quality Score, Business Criticality Distribution, Confidence Distribution, Coverage Assessment, Merged Findings, Modified Findings, Rejected Findings (+3 more)

### Community 40 - "Community 40"
Cohesion: 0.18
Nodes (10): 1. Local Development, 2. Staging Environment, 3. Production Environment, Configuration Profiles, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, EcoFleet Express Deployment Guide, Interaction Between ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS (+2 more)

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (10): 01 Infrastructure & Configuration Security Audit, 1. Executive Summary, 2. Strengths, 3.1 Weak Content Security Policy (CSP) Allows Unsafe Inline Execution, 3. Confirmed Findings, 4.1 Unverified Proxy SSL Header Trust, 4.2 Unbounded Cache Key Generation in Performance Middleware, 4. Potential Findings (+2 more)

### Community 42 - "Community 42"
Cohesion: 0.20
Nodes (3): HttpUser, EcoFleetUser, Login before starting tests

### Community 44 - "Community 44"
Cohesion: 0.20
Nodes (10): Accepted Findings, Audit Quality Score, Confidence Distribution, Coverage Assessment, Final Summary, Merged Findings, Modified Findings, Rejected Findings (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.25
Nodes (7): LOG-001: Suppressed Exception Tracebacks in Production, LOG-002: Missing Context in Security Audit Trails, LOG-003: Unlogged Authorization Failures, LOG-004: Mutable Database-Backed Audit Trails, LOG-005: Unstructured Plaintext Logging, LOG-006: Properly Mitigated Sentry PII Exposure (Informational), Phase 10A: Logging, Monitoring & Auditability (Technical Findings)

### Community 47 - "Community 47"
Cohesion: 0.25
Nodes (7): DEPLOY-001: Missing WSGI Production Server, DEPLOY-002: Missing CSRF_TRUSTED_ORIGINS for Proxy Deployment, DEPLOY-003: Single-Node Stateful Architecture, DEPLOY-004: Insecure SSL Redirect Default, DEPLOY-005: Misconfigured Referrer Policy Header, DEPLOY-006: Highly Secure X-Accel-Redirect Implementation (Informational), Phase 11A: Deployment & Production Hardening (Technical Findings)

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (5): main(), get_item(), Serialize a dictionary or list to JSON string., Safely get an item from a dictionary., to_json()

### Community 49 - "Community 49"
Cohesion: 0.33
Nodes (5): FC-001: DOM XSS via Unescaped Column Headers in Dynamic DOM Updates, FC-002: Client-Side Trust (Unvalidated `row_num` DOM State), FC-003: Weakened Content Security Policy (`unsafe-inline`), FC-004: Missing Subresource Integrity (SRI) on External CDN Assets, Phase 8A: Frontend & Client Security (Technical Findings)

### Community 51 - "Community 51"
Cohesion: 0.40
Nodes (3): URL configuration for ecofleet project.  The `urlpatterns` list routes URLs to, protected_media(), Serve media files only to authenticated staff users.     Uses X-Accel-Redirect i

### Community 52 - "Community 52"
Cohesion: 0.80
Nodes (4): apply(), current(), init(), toggle()

### Community 53 - "Community 53"
Cohesion: 0.40
Nodes (5): Architectural Evidence, Business Rule Evidence, Code Evidence, Why this is a Business Logic Vulnerability, Workflow Evidence

### Community 54 - "Community 54"
Cohesion: 0.40
Nodes (5): Architectural Evidence, Business Rule Evidence, Code Evidence, Why this is a Business Logic Vulnerability, Workflow Evidence

### Community 55 - "Community 55"
Cohesion: 0.40
Nodes (5): Architectural Evidence, Business Rule Evidence, Code Evidence, Why this is a Business Logic Vulnerability, Workflow Evidence

### Community 56 - "Community 56"
Cohesion: 0.40
Nodes (5): Architectural Evidence, Business Rule Evidence, Code Evidence, Why this is a Business Logic Vulnerability, Workflow Evidence

### Community 57 - "Community 57"
Cohesion: 0.40
Nodes (4): DEP-001: Floating Dependency Version in Third-Party CDN, DEP-002: Abandoned Security Dependency (`django-csp`), DEP-003: Mitigated XML Attack Surface (Informational), Phase 9A: Dependencies & Supply Chain Security Audit (Technical Findings)

## Knowledge Gaps
- **872 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+867 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ToolRun` connect `Community 7` to `Community 2`, `Community 37`, `Community 17`, `Community 25`, `Community 27`, `Community 29`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Why does `protected_media()` connect `Community 51` to `Community 37`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Why does `SystemEvent` connect `Community 2` to `Community 7`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `ProviderResult` (e.g. with `ActivityProvider` and `AttendanceProvider`) actually correct?**
  _`ProviderResult` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Scans the first row of the sheet to map standard keys to 1-based column indices.`, `Finds the first row containing total summaries or SUM formulas in the Amount col`, `Return paginated preview data, reading from cache if possible.` to the rest of the system?**
  _951 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.02531645569620253 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.02531645569620253 - nodes in this community are weakly interconnected._