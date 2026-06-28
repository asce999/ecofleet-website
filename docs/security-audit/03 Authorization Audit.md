# 03 Authorization Audit

## 1. Executive Summary
This document provides the findings from the Phase 3 white-box security audit, focusing exclusively on the Authorization System of the EcoFleetExpress application. The assessment analyzed role-based access controls, object-level authorization (IDOR), API endpoint protections, and horizontal/vertical privilege escalation paths.

The authorization system effectively utilizes role-based access control (RBAC) decorators to restrict tool access. However, critical vulnerabilities exist concerning vertical and horizontal privilege escalation. Administrative functions (such as modifying global salary configurations and active workbooks) are exposed to basic operators, and strict object-level authorization is missing across salary modifications and media downloads. 

**Risk Summary**
| Severity | Count |
|----------|------:|
| Critical | 1 |
| High | 1 |
| Medium | 1 |
| Low | 1 |
| Informational | 0 |

## 2. Authorization Architecture
- **Identity & Roles**: Authorization is managed via the `UserProfile` model, which uses boolean flags (`can_use_cof`, `can_use_attendance`, etc.) to grant access to specific operational modules. A `role` field determines global hierarchy (e.g., 'Employee', 'Director').
- **Enforcement Mechanisms**: Custom Python decorators (`@staff_required`, `@tool_permission_required`, `@director_required`) wrap Django views.
- **Media Protection**: Uploaded and generated files are shielded by a custom `protected_media` view that interfaces with Nginx `X-Accel-Redirect`.

## 3. Authorization Flow
1. A user requests a protected endpoint (e.g., `/portal/attendance/`).
2. `@staff_required` ensures `request.user.is_authenticated` and `request.user.is_staff`.
3. `@tool_permission_required('attendance')` queries the database for the user's `UserProfile` and checks if `profile.can_use_attendance == True`.
4. If the check fails, the user receives a warning message and is redirected to the dashboard.
5. If the check passes, the view logic executes.

## 4. Trust Boundaries
- **Unauthenticated vs. Authenticated**: Strict boundary enforced by `@staff_required` across all internal URLs.
- **Employee vs. Module**: Enforced by `@tool_permission_required`. Employees only see and access modules they are explicitly authorized for.
- **Employee vs. Director**: Enforced by `@director_required` (currently only used on the user management page).
- **Module User vs. Module Administrator**: **Broken**. Users granted access to a module are implicitly granted administrative rights over that module's global configuration.
- **Employee vs. Colleague Data**: **Broken**. Object-level checks are largely absent, allowing horizontal data modification.

## 5. Authorization Strengths
- **Fail-Closed Access**: All portal views explicitly require staff authentication; there are no default-open internal views.
- **Dynamic Permission Assignment**: The `UserProfile` model allows granular feature-flagging per employee, managed securely by Directors.
- **API Protection**: AJAX API endpoints (`btpl_api`, `ftl_api`) correctly inherit the same `@tool_permission_required` wrappers as their parent HTML views.

## 6. Confirmed Findings

### 6.1 Horizontal Privilege Escalation via Salary Calculator
**Severity**: Critical
**Confidence**: Confirmed

**Business Asset**: Payroll (Salary Overrides, Deductions, Advances)
**Likelihood**: High
**Impact**: Critical
**Verification Method**: Static Code Analysis
**Evidence Quality**: Strong

**Evidence**:
- **File**: `core/views/attendance.py`
- **Function**: `salary_calculator(request)`
- **Code Path**: The POST handler iterates through all employees and updates the `EmployeeSalaryOverride` table (`adhoc_salary_increase_pct`, `advance`, etc.) using values submitted in the request. 
- **Why**: The view is protected only by `@tool_permission_required('attendance')`. It does not verify if the user has specific HR/Payroll privileges, nor does it prevent an employee from modifying their own salary row.

**Attack Preconditions**: 
An attacker must be an authenticated staff member explicitly granted `attendance` permissions.

**Exploitation Scenario**: 
An operations clerk tasked with daily attendance marking accesses the `/portal/attendance/salary/` endpoint. They intercept the form submission and alter their own `override_inc_{name}` parameter to `50.00`, granting themselves a 50% ad-hoc salary increase prior to the monthly payroll export.

**Existing Mitigations**: None.

**False Positive Considerations**: 
It is possible that `can_use_attendance` is strictly granted only to trusted HR personnel. However, because attendance is typically a daily operational task, tying salary modification directly to attendance tracking violates the Principle of Least Privilege.

**OWASP Mapping**: A01:2021-Broken Access Control
**CWE Mapping**: CWE-639: Authorization Bypass Through User-Controlled Key

---

### 6.2 Vertical Privilege Escalation via Global Workbook Settings
**Severity**: High
**Confidence**: Confirmed

**Business Asset**: Global Configuration & Shared Operational Ledgers
**Likelihood**: High
**Impact**: High
**Verification Method**: Static Code Analysis
**Evidence Quality**: Strong

**Evidence**:
- **Files**: `core/views/attendance.py`, `core/views/btpl.py`, `core/views/ftl.py`
- **Functions**: `attendance_settings`, `btpl_settings`, `ftl_settings`
- **Code Path**: These endpoints process POST actions like `remove`, `load_default`, and `update_salary_config`.
- **Why**: These administrative actions modify the global state of the application (e.g., archiving the active shared workbook, altering global salary calculation constants in `SalaryConfig.get_solo()`). They are only protected by standard tool permissions, lacking the `@director_required` enforcement used on the user management page.

**Attack Preconditions**: 
An authenticated staff member with access to the respective tool (e.g., `can_use_ftl`).

**Exploitation Scenario**: 
An employee navigating the FTL tracker clicks the settings gear and intentionally selects "Remove Workbook." The global `FtlWorkbook` is archived (`is_active=False`), deleting the active session for the entire company and causing operational disruption.

**Existing Mitigations**: 
The records are soft-deleted (`is_active=False`) rather than permanently dropped, allowing database administrators to recover them.

**False Positive Considerations**: None. Administrative functionality is exposed to standard users.

**OWASP Mapping**: A01:2021-Broken Access Control
**CWE Mapping**: CWE-285: Improper Authorization

---

### 6.3 Authorization Bypass via Direct Media Access
**Severity**: Medium
**Confidence**: Confirmed

**Business Asset**: Generated Reports, Uploaded Workbooks, Payroll Exports
**Likelihood**: Medium
**Impact**: Medium
**Verification Method**: Static Code Analysis
**Evidence Quality**: Strong

**Evidence**:
- **File**: `core/views/media.py`
- **Function**: `protected_media(request, path)`
- **Code Path**: Validates that the file exists and belongs to `MEDIA_ROOT`, then returns the file (or an Nginx X-Accel-Redirect header) provided the user passes `@staff_required`.
- **Why**: While `core/views/common.py` uses `download_file` to strictly check `profile.can_use_{tool}` before releasing a file, `protected_media` implements no such RBAC logic.

**Attack Preconditions**: 
An authenticated staff member without specific tool permissions (e.g., a driver with no portal permissions).

**Exploitation Scenario**: 
An employee who is denied access to the Attendance/Salary module manually navigates to `/protected-media/attendance/Salary_JUNE.xlsx` (a predictable URL path). The server bypasses RBAC and streams the file, exposing the entire company's payroll data.

**Existing Mitigations**: 
Directory indexing is likely disabled, meaning attackers must guess the exact filenames (which may include timestamps or unique prefixes).

**False Positive Considerations**: 
If files are generated with highly randomized UUIDs, the likelihood of guessing paths drops significantly, but the underlying authorization bypass remains valid.

**OWASP Mapping**: A01:2021-Broken Access Control
**CWE Mapping**: CWE-425: Direct Request ('Forced Browsing')

---

## 7. Likely Findings

### 7.1 Missing Object-Level Authorization on Tool Run Modifications
**Severity**: Low
**Confidence**: Likely

**Business Asset**: Generated Reports (ToolRuns)
**Likelihood**: Low
**Impact**: Low
**Verification Method**: Static Code Analysis
**Evidence Quality**: Moderate

**Evidence**:
- **File**: `core/views/pendency.py`
- **Function**: `pendency_observations(request, pk)`
- **Code Path**: Fetches a `ToolRun` by `pk` without verifying `run.user == request.user`.
- **Why**: An attacker can submit observation CSVs to a `ToolRun` generated by another user, altering its contents.

**Attack Preconditions**: 
Staff member with `pendency` permission.

**Exploitation Scenario**: 
A user accidentally or maliciously modifies a colleague's pendency report by altering the `pk` in the URL to a report they do not own, appending inaccurate observation data.

**Existing Mitigations**: 
ToolRuns are generally treated as shared corporate assets rather than strictly private user data.

**False Positive Considerations**: 
This behavior is likely intended to support collaborative workflows where managers append observations to clerk-generated reports.

**OWASP Mapping**: A01:2021-Broken Access Control
**CWE Mapping**: CWE-639: Authorization Bypass Through User-Controlled Key

---

## 8. Potential Findings
- **Lack of Row-Level Ownership in FTL/BTPL APIs**: The `ftl_api` and `btpl_api` endpoints permit any user with the tool permission to delete any row (`action == 'delete'`), regardless of who created it. While `ToolRun` logs the deletion, the lack of row-level ownership could allow sabotage within shared ledgers.

## 9. Attack Chains
**Privilege Escalation to Payroll Exposure**
An attacker logs in using basic employee credentials. They navigate to the FTL settings page, realize global configurations are exposed, and deduce the same applies to Attendance. They navigate to `/portal/attendance/settings/`, modify the `SalaryConfig` to elevate specific allowances, generate a new salary export, and download it. Alternatively, they directly query the predictable media endpoint for the exported salary Excel file, bypassing RBAC entirely.

## 10. Hardening Recommendations
1. **Decouple Data Entry from Administration**: Create a new permission flag (e.g., `is_hr` or `is_tool_admin`) or rely on `@director_required` to protect the `salary_calculator`, `salary_calculator_export`, and all `*_settings` endpoints. 
2. **Enforce RBAC on Direct Media Access**: Refactor `protected_media` in `media.py` to intercept the file request, map the directory path (e.g., `/attendance/`) to the corresponding tool permission, and deny access if `getattr(profile, f"can_use_{tool}", False)` is false.
3. **Validate Employee Context**: Within `salary_calculator`, ensure users cannot submit `EmployeeSalaryOverride` values for their own `employee_name` unless they possess higher-level administrative privileges.
4. **Implement UUIDs for File Names**: Ensure `ToolRunFile` and `*Workbook` file names are appended with cryptographically secure random strings to prevent predictable media paths.

## 11. Authorization Security Score (0–10)
**Score: 4/10**
While baseline RBAC exists, critical missing boundaries regarding administrative tool access, payroll modification, and media retrieval drastically lower the overall score.

## 12. Overall Risk Rating
**Critical**
The ability for basic operators to alter their own salaries and bypass RBAC to download highly sensitive Excel files constitutes an immediate, critical business risk.

## 13. Authorization Maturity Assessment
**Level: Initial (Level 1)**
The application applies RBAC at the macro-level (View layer) but fails to apply micro-level authorization (Object-level, Action-level, Media-level). The system requires significant refactoring to decouple administrative capabilities from standard operational permissions before it can reach a Defined (Level 2) maturity.
