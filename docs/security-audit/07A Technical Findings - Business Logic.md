## ID

BL-001

---

## Title

Financial Manipulation via Unbounded `payable_days` Extraction

---

## Severity

Critical

---

## Confidence

Confirmed

Explain why.
The code in `core/attendance.py` explicitly parses `payable_days_from_sheet` directly from the user-supplied Excel workbook and uses it to calculate the `basic` salary multiplier without validating it against the physical number of days in the month.

---

## Business Criticality

Mission Critical

Explain why.
This directly impacts the core financial integrity of the company. It allows an authorized insider (e.g., HR staff) to arbitrarily multiply an employee's salary payout with no system-level checks or bounds.

---

## Affected Components

- Provider: `core/attendance.py`
- Function: `get_attendance_data`, `calculate_salary_data`
- Workbook: `Attendance_Sheet.xlsx`

---

## Evidence

- File: `core/attendance.py`
- Function: `get_attendance_data` (Lines 152-156), `calculate_salary_data` (Lines 349-354)
- Execution Flow:
  1. `get_attendance_data` parses the 'Payable Days' column.
  2. `payable_days_from_sheet = float(val)`.
  3. `calculate_salary_data` checks `if sheet_payable_days is not None: payable_days = Decimal(str(sheet_payable_days))`.
  4. `basic = my_round(payable_days * config.basic_rate_per_day)`.

Explain why the evidence supports the finding.
The code bypasses the computed attendance (Present + Half Days) entirely if a value is typed into the "Payable Days" column. There is no `min()` or bounds check against `days_in_month`. If the column contains 999, the employee receives 999 days of basic pay for a single month.

---

## Technical Description

The attendance processing logic computes `payable_days` by counting the attendance codes ('P', 'HD', 'A'). However, if the "Payable Days" column in the Excel sheet contains a numeric value, this value overrides the computed logic. The script trusts this value unconditionally and casts it to a `float` without verifying that it is less than or equal to the total days in the month. 

---

## Business Impact

Severe financial loss. An authorized but malicious HR employee can artificially inflate salaries to embezzle funds or drastically overpay employees.

---

## Exploit Scenario

An insider with FTL/Attendance tool access downloads the active `Attendance_Sheet.xlsx`. They modify the "Payable Days" cell for their own row to `500.0`. They re-upload the workbook. When the salary calculator runs, their basic pay, allowances, and net payment are multiplied by 500, resulting in a massively inflated payout that the system incorrectly signs off as valid.

---

## Root Cause

- Trust Assumption
- Missing Business Validation

---

## Why this is a Business Logic Vulnerability

### Code Evidence
Line 354: `payable_days = Decimal(str(sheet_payable_days))` unconditionally overrides `computed_payable_days`.

### Workflow Evidence
The system workflow trusts the uploaded Excel file as the absolute source of truth for overrides, completely bypassing the daily attendance logging.

### Business Rule Evidence
A core business rule dictates that payable days in a single month cannot exceed the number of days in that month (e.g., 31). This rule is absent.

### Architectural Evidence
The architecture decoupled the data storage (Excel) from the constraints (Database), leaving no relational constraints to prevent impossible states.

---

## Cross-Phase References

- 04 File Upload & Workbook Security Audit.md (Workbook Trust Assumptions)

---

## Counter Argument

Could this be intentional for handling arrears or advance payments?
If the company intended to pay for previous unpaid months, they might legitimately need `payable_days > 31`. However, the system has dedicated fields in the `EmployeeSalaryOverride` model for `advance`, `cash_payment`, and `adhoc_allowance`. Overloading `payable_days` breaks all statutory calculations (PF, ESIC, PT) which are capped or banded based on standard monthly ceilings. It is highly unlikely this is intentional.

---

## Confidence Review

Confirmed. The code explicitly shows the lack of validation and the direct mathematical impact on the final salary output.

---

## Exploit Complexity

Low

Explain why.
It requires only basic Excel editing skills and authorization to use the attendance module. No technical hacking tools are required.

---

## Detection Difficulty

Medium

Explain why.
The inflated value would appear on the final generated salary slip and total cost reports, which a finance director might notice if they scrutinize the aggregate totals. However, it is not flagged or prevented by the system itself.

---

## ID

BL-002

---

## Title

Missing Terminal State Guard in Morning Report Orchestration

---

## Severity

High

---

## Confidence

Confirmed

Explain why.
The `update_existing_rows` function in `core/morning.py` unconditionally overwrites the master workbook's `Status` column, unlike its counterpart in `core/prev_month.py` which explicitly skips rows that are already "Delivered".

---

## Business Criticality

Important

Explain why.
Logistics operations rely on accurate terminal states. If a shipment is marked "Delivered", it triggers downstream invoicing and customer notifications. Reverting it back to "In Transit" corrupts historical data and reporting.

---

## Affected Components

- Provider: `core/morning.py`
- Function: `update_existing_rows`
- Workbook: `2W Report` / `CV Report`

---

## Evidence

- File: `core/morning.py`
- Function: `update_existing_rows`
- Execution Flow: 
  1. `master_df.iterrows()` iterates over all existing shipments.
  2. `rep = report_lookup.loc[lr]` finds the matching LRN in the uploaded CSV.
  3. `status = rep["Status_mapped"]`
  4. `master_df.at[idx, "Status"] = status`

Explain why the evidence supports the finding.
There is no `if current_status == "Delivered": continue` guard. The system implicitly trusts that the daily Delhivery CSV will never contain older, regressed statuses for previously completed shipments.

---

## Technical Description

The Morning Report generation cross-references the active Master workbook against newly uploaded CSV dumps from Delhivery. While the Previous Month report (`prev_month.py`) correctly guards terminal states (ensuring "Delivered" shipments are not reverted to "In Transit"), the `morning.py` module blindly applies whatever status the CSV provides.

---

## Business Impact

Operational confusion and corrupted logistics history. Previously closed shipments can re-appear as pending, causing false SLA alerts and potentially delaying vendor payments.

---

## Exploit Scenario

An insider wants to delay SLA breach metrics for a specific vehicle. They manually edit the daily Delhivery CSV dump before uploading it to EcoFleet, changing a previously "Delivered" shipment back to "In Transit" (or uploading an older CSV). The Morning Report logic blindly accepts this, reverting the state in the Master workbook.

---

## Root Cause

- Missing State Validation
- Trust Assumption

---

## Why this is a Business Logic Vulnerability

### Code Evidence
Line 198-208 in `morning.py` executes the status overwrite with no conditional checks on the previous state of the row.

### Workflow Evidence
The workflow assumes that the external logistics provider's (Delhivery) daily CSV is perfectly sequential and never includes regressed data.

### Business Rule Evidence
A package cannot logically transition from "Delivered" back to "In Transit" in standard logistics workflows.

### Architectural Evidence
The inconsistency between `morning.py` (vulnerable) and `prev_month.py` (patched) demonstrates a lack of centralized state machine enforcement.

---

## Cross-Phase References

None.

---

## Counter Argument

Could the business intentionally require reverting statuses if Delhivery made a mistake?
Yes, external logistics providers occasionally correct false delivery events. If so, reverting to "In Transit" might be intentional. However, `prev_month.py` actively prevents this, showing that the system's design intent is to treat "Delivered" as terminal. The inconsistency proves it is a flaw.

---

## Confidence Review

Confirmed. The code explicitly shows the unconditional status overwrite.

---

## Exploit Complexity

Low

Explain why.
An insider simply needs to edit a standard CSV file before uploading it to the portal.

---

## Detection Difficulty

Hard

Explain why.
The system does not maintain an audit trail of row-level state changes, meaning the regression would go unnoticed unless a human visually catches the discrepancy in the vast Excel sheet.

---

## ID

BL-003

---

## Title

Ghost Records via Partial Execution in COF Generation

---

## Severity

Medium

---

## Confidence

Confirmed

Explain why.
The architecture performs a persistent filesystem mutation (saving the workbook) before confirming the database state (`ToolRun.objects.create`).

---

## Business Criticality

Important

Explain why.
Certificate of Facts (COF) sequence numbers (e.g., EFE-COF-0010) are legally and operationally significant. Skipped or missing sequence numbers cause audit failures during claims processing.

---

## Affected Components

- Provider: `core/cof.py`
- Service: `core/views/cof.py`
- Workbook: COF Tracking Workbook

---

## Evidence

- File: `core/cof.py` (Line 334), `core/views/cof.py` (Line 53)
- Execution Flow:
  1. `cof_logic.generate_cof` writes to the Excel workbook and saves it.
  2. The function returns to `views/cof.py`.
  3. `ToolRun.objects.create` attempts to save the database record.

Explain why the evidence supports the finding.
If step 3 fails (e.g., due to a database lock, network timeout, or server restart), step 1 has already persistently mutated the state of the active COF Workbook. 

---

## Technical Description

The COF generator implements a custom filesystem lock (`workbook_lock`) to prevent concurrent writes to the Excel sheet. It determines the next COF sequence number, writes the new certificate details to the sheet, and saves the file. It then returns execution to the Django view, which finally registers the `ToolRun` in the PostgreSQL database. There is no distributed transaction or rollback mechanism covering both the filesystem and the database.

---

## Business Impact

Audit compliance failure. The Excel workbook will show that `EFE-COF-0015` was generated, but the EcoFleet database will have no record of it, and the user will never receive the `.docx` file.

---

## Exploit Scenario

A user submits the COF form. The server successfully modifies the Excel file. Exactly at that moment, the PostgreSQL connection pool is exhausted or restarts. The `ToolRun` creation fails. The user receives a 500 Error. They retry. The system issues `EFE-COF-0016`. `EFE-COF-0015` remains as a "ghost record" in the Excel tracking sheet, forever disconnected from the portal's audit logs.

---

## Root Cause

- Missing Transaction
- Workflow Design

---

## Why this is a Business Logic Vulnerability

### Code Evidence
The mutation `wb.save(workbook_path)` happens independently and prior to the database transaction.

### Workflow Evidence
The system lacks a two-phase commit or compensation action to roll back the Excel changes if the subsequent database write fails.

### Business Rule Evidence
Claims processing requires strict sequential integrity. Missing sequence numbers trigger compliance alerts.

### Architectural Evidence
Mixing non-transactional storage (Filesystem/Excel) with transactional storage (Database) without an orchestrator creates inherent partial execution risks.

---

## Cross-Phase References

- 05 Storage & Database Audit.md (Lack of Atomicity)

---

## Counter Argument

Can the user just manually delete the ghost record from the Excel sheet?
Yes, but they must download the active workbook, manually edit it, delete the active tracking workbook in the portal, and upload the corrected one. This is a severe operational burden and risks further data corruption.

---

## Confidence Review

Confirmed. The lack of rollback logic between the filesystem save and the database save guarantees this edge case will occur under fault conditions.

---

## Exploit Complexity

High

Explain why.
It is difficult to intentionally trigger a precise race condition or database fault exactly between the two function calls. It is more likely to occur organically as an operational fault.

---

## Detection Difficulty

Medium

Explain why.
The discrepancy is detectable if an auditor actively compares the maximum sequence number in the Excel sheet against the `ToolRun` records in the database.

---

## ID

BL-004

---

## Title

Arbitrary Data Overwrite via Unvalidated Row Index in Shipment APIs

---

## Severity

High

---

## Confidence

Confirmed

Explain why.
The `add_ftl_shipment` function unconditionally writes to the row specified by the `row_num` argument without verifying if the row is already occupied.

---

## Business Criticality

Business Critical

Explain why.
Allows authorized users to silently corrupt existing logistical records, which can hide SLA breaches, alter billing details, or sabotage operations.

---

## Affected Components

- Provider: `core/ftl.py`, `core/btpl.py`
- Service: `add_ftl_shipment`, `add_btpl_shipment`
- APIs: `ftl_api`, `btpl_api`

---

## Evidence

- File: `core/ftl.py`
- Function: `add_ftl_shipment` (Line 116)
- Execution Flow:
  1. API receives `row_num`.
  2. Passes `row_num` to `add_ftl_shipment`.
  3. `row = row_data['row_num']`.
  4. `sheet.cell(row=row, column=col).value = clean(val)`.

Explain why the evidence supports the finding.
There is absolutely no check to ensure `sheet.cell(row=row, column=col).value` is `None` or empty before overwriting it.

---

## Technical Description

When appending a new shipment via the FTL or BTPL interface, the client sends a `row_num` hidden input indicating the target row. The backend `add_ftl_shipment` function uses this index to directly access the `openpyxl` sheet and write the new data. It does not perform a "dirty check" to see if the row already contains data belonging to another shipment.

---

## Business Impact

Silent data corruption. Historical or pending shipments can be overwritten with new data, destroying the original record without any audit trail.

---

## Exploit Scenario

An insider wants to sabotage a specific vendor's billing. They intercept the AJAX request for a new FTL shipment they are creating. They change `row_num` to point to a row containing a completed, high-value shipment from last week. The backend blindly overwrites the old shipment with the new shipment data.

---

## Root Cause

- Trust Assumption
- Missing Business Validation

---

## Why this is a Business Logic Vulnerability

### Code Evidence
Line 133: `sheet.cell(row=row, column=col).value = clean(val)` executes unconditionally.

### Workflow Evidence
The server delegates the responsibility of finding the "next empty row" entirely to the client's initial page load (via `find_next_ftl_row`), and then trusts the client's assertion during the subsequent POST.

### Business Rule Evidence
Records should be immutable once delivered, and new records should exclusively append.

### Architectural Evidence
This is a classic "Trusting the Client" flaw applied to a business orchestration workflow.

---

## Cross-Phase References

- 06A Technical Findings - Views & APIs.md (Unbounded Row Input)

---

## Counter Argument

Doesn't `find_next_ftl_row` prevent this?
`find_next_ftl_row` is only used when rendering the initial form via `get_ftl_page_data` (GET request). When the user submits the form via `ftl_api` (POST request), the backend uses the user-submitted `row_num` directly without re-verifying if the row is still empty. 

---

## Confidence Review

Confirmed. The separation of the "find next row" logic (GET) and the "write to row" logic (POST) without server-side re-validation explicitly proves the flaw.

---

## Exploit Complexity

Low

Explain why.
An insider simply modifies the `row_num` field in their browser's Developer Tools before submitting the form.

---

## Detection Difficulty

Hard

Explain why.
Because the system lacks an independent database of shipments (relying entirely on the Excel workbook as the source of truth), overwritten rows are permanently destroyed with no history or diffs.
