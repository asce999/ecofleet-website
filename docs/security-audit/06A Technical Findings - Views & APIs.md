## ID

VIEW-001

---

## Severity

Critical

---

## Confidence

Confirmed

Explain why.
The source code in `core/views/media.py` clearly demonstrates that `protected_media` only invokes `@staff_required`. No Role-Based Access Control (RBAC) decorators are applied, despite the files served containing restricted operational data.

---

## Affected Components

Views

URLs

Files

---

## Evidence

- file: `core/views/media.py`
- function: `protected_media`
- execution path: `urls.py -> protected_media -> FileResponse`

---

## Technical Description

The `protected_media` view routes all requests for files inside `MEDIA_ROOT`. It implements `@staff_required` and path traversal checks. However, it completely omits any validation against the user's `UserProfile` RBAC flags (e.g., `can_use_attendance`, `can_use_ftl`). Because the application stores sensitive Excel workbooks in predictable locations (e.g., `attendance/Attendance_Sheet.xlsx`), any user with baseline staff access can download any file globally.

---

## Exploit Path

1. Attacker (with low-privilege staff access) logs into the portal.
2. Attacker directly requests the URL `/media/ftl/FTL_Shipment_Tracker.xlsx` or `/media/attendance/Attendance_Sheet.xlsx`.
3. The server processes the request via `protected_media`, which only checks if the user is staff.
4. The server returns the file via `FileResponse` or `X-Accel-Redirect`.
5. The attacker gains full access to restricted company data, entirely bypassing the application's RBAC system.

---

## Root Cause

Missing Authorization

---

## Cross-Phase References

05 Storage & Database Audit.md (Predictable Storage Locations)
03 Authorization Audit.md (RBAC Bypass)

---

## Why this is exploitable

Code
The `protected_media` function has no checks against the `UserProfile` access control flags.

Framework
Django's `FileResponse` serves the file without invoking custom middleware if the view doesn't explicitly validate permissions.

Architecture
Relying on view-level decorators for HTML pages while exposing the underlying assets through a generic static handler creates an unmitigated IDOR.

---

## Self-Correction

Challenge your own conclusion.
Could this be intentional? Perhaps the developer assumed staff members inherently trust each other? 
No. The presence of `@director_required` and granular tool permissions on UI endpoints explicitly proves that data compartmentalization between staff members is a core business requirement.

---

## Confidence Review

Confirmed. The source code clearly shows only a single `@staff_required` check on the view, exposing all media assets.

---

## ID

VIEW-002

---

## Severity

High

---

## Confidence

Confirmed

Explain why.
The hardcoded dictionary `tool_map` in `core/views/common.py` is definitively missing the `FTL` key, causing the dictionary lookup to fail-open and skip the permission check.

---

## Affected Components

Views

Functions

URLs

---

## Evidence

- file: `core/views/common.py`
- function: `download_file`
- execution path: `urls.py -> download_file -> ToolRunFile -> FileResponse`

---

## Technical Description

The `download_file` view is the authorized method for downloading `ToolRunFile` outputs. It checks permissions using a hardcoded `tool_map` dictionary that maps ToolRun types to permissions (e.g., `'COF': 'cof'`). However, `ToolRun.TOOL_FTL` ('FTL') is missing from `tool_map`. If `tool_map.get(f.run.tool)` returns `None`, the authorization condition `if required_perm and not getattr(...)` silently fails-open. 

---

## Exploit Path

1. Attacker (without FTL permissions) discovers the `file_id` of an FTL report.
2. Attacker issues a GET request to `/portal/download/<file_id>/`.
3. `download_file` evaluates `tool_map.get('FTL')`, which returns `None`.
4. The permission check `if required_perm and not getattr(...)` evaluates to False because `required_perm` is `None`.
5. The view returns the file, bypassing RBAC.

---

## Root Cause

Missing Authorization

---

## Cross-Phase References

03 Authorization Audit.md (Fail-Open Authorization Logic)

---

## Why this is exploitable

Code
`tool_map` omits the `'FTL': 'ftl'` key, leading to a silent failure.

Framework
The standard python dictionary `.get()` returns `None` for missing keys, causing the boolean check to short-circuit in a fail-open manner.

Architecture
Hardcoded permission mappings decoupled from the database or the models lead to synchronization errors when new features are added.

---

## Self-Correction

Challenge your own conclusion.
Could this be intentional? 
No. `FTL` is correctly present in the `tool_map` in the `tool_result()` function directly below it in the exact same file. The omission in `download_file()` is an oversight.

---

## Confidence Review

Confirmed. The code explicitly shows the missing key and the resultant fail-open execution path.

---

## ID

VIEW-003

---

## Severity

High

---

## Confidence

Confirmed

Explain why.
The Django form fields for `row_num` in `BtplShipmentForm` and `FtlShipmentForm` explicitly lack `max_value` limits. The `openpyxl` library's memory behavior when writing to high row indices is well documented.

---

## Affected Components

Forms

Views

APIs

---

## Evidence

- file: `core/forms.py`, `core/ftl.py`, `core/views/ftl.py`
- function: `ftl_api`, `add_ftl_shipment`
- execution path: `POST /portal/ftl/api/ -> FtlShipmentForm.clean() -> add_ftl_shipment -> openpyxl load/save`

---

## Technical Description

The `btpl_api` and `ftl_api` endpoints handle `action=save` operations using `BtplShipmentForm` and `FtlShipmentForm`. These forms capture the target `row_num` as a simple, unbounded `IntegerField(widget=forms.HiddenInput())`. The view passes this value directly to `openpyxl`, which accesses `sheet.cell(row=row_num)` and saves the file. 

---

## Exploit Path

1. Attacker initiates an FTL or BTPL shipment save request via the AJAX API.
2. Attacker modifies the POST payload to set `row_num=1048576` (the maximum allowed row limit in Excel).
3. The server validates the form (which has no upper bounds check) and passes the row number to `openpyxl`.
4. `openpyxl` opens the workbook and dynamically allocates internal XML structures up to row 1,048,576.
5. When `openpyxl` serializes the massive XML tree back to disk, it consumes gigabytes of memory.
6. The Python process crashes with an Out Of Memory (OOM) error, causing a Denial of Service.

---

## Root Cause

Missing Validation

---

## Cross-Phase References

04 File Upload and Workbook Audit.md (Third-Party Parser Memory Exhaustion)

---

## Why this is exploitable

Code
The `row_num = forms.IntegerField(widget=forms.HiddenInput())` definition lacks a `max_value` argument.

Framework
Django Forms accept any valid integer up to system limits if bounds aren't explicitly specified.

Architecture
Allowing client-side hidden values to dictate server-side memory allocations through expensive third-party parsers exposes the system to trivial resource exhaustion.

---

## Self-Correction

Challenge your own conclusion.
Could `openpyxl` handle this gracefully? 
No, `openpyxl` is inherently DOM-based when modifying existing files. Writing to the absolute end of an empty sheet forces the library to pad the internal data structures, which is a known vector for OOM Denial of Service attacks.

---

## Confidence Review

Confirmed. The lack of Django bounds validation and the physical limits of `openpyxl` memory allocation guarantee this exploit works.

---

## ID

VIEW-004

---

## Severity

High

---

## Confidence

Confirmed

Explain why.
The loop inside `salary_calculator` performs individual `update_or_create` calls, and `DATABASES` in `settings.py` does not have `ATOMIC_REQUESTS` enabled.

---

## Affected Components

Views

Functions

---

## Evidence

- file: `core/views/attendance.py`
- function: `salary_calculator`
- execution path: `POST /portal/attendance/salary/ -> for emp in data: update_or_create`

---

## Technical Description

The `salary_calculator` function iterates over an array of employee data to perform multiple sequential database `update_or_create` operations for salary records. This loop is not wrapped in an explicit `transaction.atomic()` block.

---

## Exploit Path

1. An authorized Admin submits a large batch of salary overrides via the UI.
2. The server begins processing, successfully committing the first half of the records to the database.
3. The server encounters a database lock, network error, or invalid data string on the remaining records.
4. The unhandled exception aborts the request.
5. The database is left in a partially updated state, causing severe financial data corruption requiring manual reconciliation.

---

## Root Cause

Architecture

---

## Cross-Phase References

05 Storage & Database Audit.md (Missing Atomicity)

---

## Why this is exploitable

Code
The batch processing loop is missing a `with transaction.atomic():` context manager.

Framework
Django operates in autocommit mode by default; each `update_or_create` commits immediately to the database unless wrapped in a transaction block.

Architecture
Financial operations are inherently transactional. Implementing them iteratively without transaction isolation breaks database consistency guarantees.

---

## Self-Correction

Challenge your own conclusion.
Could Django's `ATOMIC_REQUESTS` be enabled globally, rendering this safe? 
I verified `core/settings.py` — `ATOMIC_REQUESTS` is not present in the `DATABASES` configuration. The vulnerability is real.

---

## Confidence Review

Confirmed. The absence of `transaction.atomic` combined with default autocommit behavior makes this a guaranteed data integrity failure under fault conditions.
