# Phase 7B — Business Logic Peer Review

---

## Finding ID
BL-001

---

## Decision
Accept

---

## Confidence Review
Confirmed. The absence of bounds checking on `payable_days_from_sheet` is explicitly visible in `core/attendance.py`, and the arithmetic operations inside `calculate_salary_data` prove that the lack of clamping directly inflates the final computed salary.

---

## Severity Review
Critical. This directly allows financial manipulation and theft by an authorized insider, with zero system-level limits. An external security auditor would universally agree on Critical severity given the monetary impact and ease of exploitation.

---

## Business Criticality Review
Mission Critical. It targets the primary financial output of the HR component. Embezzlement or gross overpayment threatens the business's financial health.

---

## Reviewer Confidence
Very High. The math and code flow are indisputable.

---

## Evidence Review
Strong. The code explicitly shows the extraction of `float(val)` and the overriding of the legitimately computed `payable_days` without `min()` clamping.

---

## Assumptions
- We assume that `payable_days` should not legitimately exceed the physical days in the month (e.g., 31). This is a safe assumption given that advances and arrears are handled through separate explicit fields in the `EmployeeSalaryOverride` model.

---

## Counter Evidence
None.

---

## Missing Evidence
None. The code snippet showing the calculation `payable_days = Decimal(str(sheet_payable_days))` is sufficient.

---

## Reviewer Notes
The original auditor correctly identified the separation between the storage (Excel) and the constraints (Database). Overloading the `payable_days` column for arrears instead of using the dedicated `adhoc_allowance` or `cash_payment` fields is an anti-pattern. This is a textbook trust boundary violation.

---

## Final Decision
Accept as Critical.

---

## Finding ID
BL-002

---

## Decision
Accept

---

## Confidence Review
Confirmed. The comparison between `morning.py` (which blindly applies updates) and `prev_month.py` (which actively guards against modifying "Delivered" shipments) proves that terminal state guarding is an intended business rule that was improperly omitted in the daily sync logic.

---

## Severity Review
High. Modifying terminal states ("Delivered" -> "In Transit") corrupts operational metrics, SLA reporting, and historical tracking. Since it requires insider access to upload a manipulated CSV, High is appropriate.

---

## Business Criticality Review
Important. While it does not result in direct financial theft, it heavily disrupts the integrity of logistics operations and SLA tracking.

---

## Reviewer Confidence
Very High. The side-by-side evidence of the two modules is conclusive.

---

## Evidence Review
Strong. The lack of a conditional check `if current_status == "Delivered": continue` in `update_existing_rows` is directly observable.

---

## Assumptions
- We assume that "Delivered" is a terminal state. This is verified by the existence of the guard in the closely related `prev_month.py` module.

---

## Counter Evidence
Delhivery might legitimately send a correction if a shipment was mistakenly marked delivered. However, if this was the intended workflow, `prev_month.py` would not explicitly block it.

---

## Missing Evidence
None.

---

## Reviewer Notes
Excellent correlation finding. Spotting the discrepancy between `morning.py` and `prev_month.py` proves the omission was a flaw rather than an intended feature. This finding will easily survive external review.

---

## Final Decision
Accept as High.

---

## Finding ID
BL-003

---

## Decision
Accept

---

## Confidence Review
Confirmed. The `generate_cof` function performs a persistent filesystem mutation (saving the workbook), and only after returning to the view does it attempt a database insert. If the DB insert fails, the filesystem is not rolled back.

---

## Severity Review
Medium. The operational impact is a skipped sequence number in the database and a ghost record in the workbook. While annoying and problematic for audits, it doesn't allow privilege escalation, RCE, or direct theft.

---

## Business Criticality Review
Important. COF sequence numbers have legal and audit significance for claims processing.

---

## Reviewer Confidence
High. The lack of distributed transaction logic is clear.

---

## Evidence Review
Strong. The sequence of operations (filesystem write followed by independent database write without a try/finally rollback block) guarantees this edge case will occur.

---

## Assumptions
- We assume that the database can occasionally fail or time out after the filesystem write completes. This is a fundamental law of distributed systems.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
This is a classic "partial execution" vulnerability stemming from mixing non-transactional (Excel) and transactional (PostgreSQL) datastores. The original auditor rightly identified this. A compensation action (e.g., rolling back the Excel file if the DB fails) is mandatory here.

---

## Final Decision
Accept as Medium.

---

## Finding ID
BL-004

---

## Decision
Accept

---

## Confidence Review
Confirmed. The `add_ftl_shipment` function takes `row` directly from the user's `row_data['row_num']` payload and unconditionally executes `sheet.cell(row=row, column=col).value = clean(val)`. 

---

## Severity Review
High. It allows authorized users to silently overwrite historical or pending shipment records, completely destroying the original data without an audit trail.

---

## Business Criticality Review
Business Critical. The ability to arbitrarily delete/overwrite shipments compromises the core logistical tracking database (the FTL Excel sheet).

---

## Reviewer Confidence
Very High. The code lacks any "dirty checking" or `if cell.value is None` validation.

---

## Evidence Review
Strong. The separation of the "find next empty row" logic in the GET request and the blind trust of `row_num` in the POST request is a textbook example of a Business Logic Trust Assumption flaw.

---

## Assumptions
None. The code undeniably overwrites whatever is in that row.

---

## Counter Evidence
None.

---

## Missing Evidence
None.

---

## Reviewer Notes
This finding perfectly highlights the dangers of relying on the client to dictate backend state (e.g., "put this in row 2"). The backend must re-verify that row 2 is actually empty before writing, or simply calculate the next empty row itself during the POST request. Excellent finding.

---

## Final Decision
Accept as High.

---

# Review Metrics

## Accepted Findings
4

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
- Confirmed: 4
- Likely: 0
- Potential: 0

---

## Severity Distribution
- Critical: 1
- High: 2
- Medium: 1
- Low: 0

---

## Business Criticality Distribution
- Mission Critical: 1
- Business Critical: 1
- Important: 2
- Minor: 0

---

## Audit Quality Score
Score: 9.5/10
Explain why: The original auditor strictly followed the constraints (technical facts only, no recommendations) and identified extremely relevant, domain-specific logic flaws (financial rounding/limits, state machine transitions, partial execution, and unvalidated client input). The evidence provided is robust, and the correlation between different modules (e.g., `morning.py` vs `prev_month.py`) shows a deep understanding of the application's architecture.

---

## Coverage Assessment
- Coverage %: ~95% of core business logic paths.
- Blind Spots: We did not deeply audit the business logic surrounding the `ToolRun` overrides or how specific `ToolRunFile` artifacts are tied to individual shipments beyond COF. 
- Remaining Risks: The heavy reliance on Excel workbooks as the primary datastore for FTL/BTPL/Attendance means there could be hidden race conditions if multiple users submit POST requests simultaneously, even outside of the COF lock.

---

## Reviewer Recommendations

- Evidence quality is excellent; keep focusing on direct code snippets to prove trust assumptions.
- Classification is spot on. The distinction between Technical Debt and a true Business Logic flaw (like BL-002) is well articulated.
- Threat modelling realistically captures insider threats (e.g., HR staff inflating salaries, logistics staff hiding SLA breaches).
- For future audits, pay closer attention to concurrent POST requests in modules that lack the `workbook_lock` (e.g., `add_ftl_shipment` might not just have overwrite issues via `row_num`, but also race conditions if two users submit the form simultaneously).
