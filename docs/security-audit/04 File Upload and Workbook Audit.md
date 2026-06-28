# Phase 4: File Upload & Workbook Security Audit

## Overview
This document represents Phase 4 of the comprehensive security audit, focusing on the application's file upload pipelines and workbook handling logic. The audit reviewed `core/forms.py` (validation logic), upload endpoints in `core/views/`, and the workbook generation/mutation modules (`btpl.py`, `ftl.py`, `attendance.py`, `cof.py`).

## Summary of Findings

### Confirmed Vulnerabilities
1. **[High]** XML Decompression Bomb (ZIP Bomb) in XLSX Uploads
2. **[High]** Unrestricted File Size leading to OOM (Denial of Service) via CSV Uploads
3. **[High]** Formula Injection (CSV / Excel Injection) in Workbook Writes
4. **[Medium]** Data Integrity Loss via Concurrent Workbook Modifications

### Evaluated False Positives
1. **XML External Entity (XXE) / Billion Laughs Attack via `openpyxl`**
2. **Path Traversal / Header Injection via `original_name` in Uploaded Files**

---

## Detailed Findings

### 1. XML Decompression Bomb (ZIP Bomb) in XLSX Uploads
- **Severity:** High
- **Confidence:** High (Confirmed by source code review of `openpyxl` usage and validation thresholds).
- **Business Asset:** Server Availability.
- **Likelihood:** Medium
- **Impact:** High (Denial of Service / OOM crashing the Django worker).
- **Verification Method:** Code Review
- **Evidence Quality:** Strong

**Evidence:**
In `core/forms.py`:
```python
def validate_xlsx_upload(f):
    max_size = 10 * 1024 * 1024 # 10 MB
    if f.size > max_size:
        raise forms.ValidationError("File too large. Maximum size is 10MB.")
```
In `core/cof.py`, `core/btpl.py`, `core/ftl.py`, `core/attendance.py`:
```python
# Typically loaded without limits on decompressed sizes
wb = openpyxl.load_workbook(file_path, data_only=False)
```

**Why this is a Vulnerability:**
Excel `.xlsx` files are ZIP archives containing XML. While a 10MB limit restricts the uploaded archive size, a malicious 10MB ZIP can contain over 10GB of highly compressed XML data. Because `openpyxl` reads the entire DOM structure into memory when `data_only=False` (or defaults) is used, attempting to parse this file will exhaust server memory and kill the Django worker process.

**Counter Argument (Pass 2 Challenge):**
*Doesn't the 10MB file limit prevent DoS?*
No. ZIP files can achieve extreme compression ratios for repetitive data (often >1000:1). 10MB of compressed data is more than enough to overwhelm the available RAM of standard application servers when expanded into an XML DOM tree.

**Attack Preconditions:**
- The attacker must have access to a tool that accepts `.xlsx` uploads (e.g., COF tracking workbook, FTL/BTPL trackers).

**Exploitation Scenario:**
1. A malicious insider crafts a zip bomb disguised as an `.xlsx` file, ensuring its compressed size is 9.9MB.
2. They upload it via the portal.
3. The server begins processing the file via `openpyxl.load_workbook()`.
4. The memory usage spikes into gigabytes, triggering an Out-of-Memory (OOM) killer that terminates the web server process, causing downtime.

**Existing Mitigations:**
- A 10MB limit on the compressed archive size. This fails because it does not restrict the *decompressed* size or memory consumption of the DOM tree.

**Recommended Fix:**
Use a secure XML parser configuration or `zipfile` hooks to reject archives that decompress beyond a safe threshold (e.g., 50MB uncompressed). `defusedxml` does not limit total decompressed size natively for Zip bombs. Alternatively, parse `.xlsx` files in a Celery background worker with strict memory limits so it doesn't crash the main web application, or use `read_only=True` in `openpyxl` if mutation is not strictly necessary.

**Mapping:**
- OWASP: A04:2021 – Insecure Design
- CWE: CWE-409 (Improper Handling of Highly Compressed Data (Data Amplification))


### 2. Unrestricted File Size leading to OOM (Denial of Service) via CSV Uploads
- **Severity:** High
- **Confidence:** High (Confirmed by source code review of `morning.py` and `pendency.py` views).
- **Business Asset:** Server Availability.
- **Likelihood:** Medium
- **Impact:** High (Denial of Service / OOM).
- **Verification Method:** Code Review
- **Evidence Quality:** Strong

**Evidence:**
In `core/views/morning.py`:
```python
delhivery_files = request.FILES.getlist('delhivery_files')
if not delhivery_files:
    messages.error(request, "Upload at least one Delhivery CSV.")
```
In `core/pendency.py`:
```python
def load_observation_csvs(files):
    for f in files:
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
```

**Why this is a Vulnerability:**
The application relies on `validate_xlsx_upload` for `.xlsx` limits, but completely omits file size validation for `.csv` uploads (Delhivery and observation files). `pandas.read_csv()` loads the entire file and all its string data into memory. A malicious user can upload a multi-gigabyte CSV file, resulting in immediate memory exhaustion.

**Counter Argument (Pass 2 Challenge):**
*Doesn't Django enforce a global `DATA_UPLOAD_MAX_MEMORY_SIZE`?*
Django enforces `FILE_UPLOAD_MAX_MEMORY_SIZE` (default 2.5MB) to determine when to spool files to disk versus keeping them in RAM. It does *not* limit the total upload size by default; it only limits how much is kept in memory *before* parsing. `pandas` will still read the multi-gigabyte spooled file from disk into RAM.

**Attack Preconditions:**
- The attacker must have access to the Morning Report or Pendency Report generation features.

**Exploitation Scenario:**
1. Attacker generates a 5GB CSV file containing junk data.
2. Attacker uploads it via the Morning Report page.
3. Django spools it to disk, then passes the file handle to `pandas.read_csv()`.
4. Pandas allocates massive amounts of memory to parse the rows, crashing the Django worker.

**Existing Mitigations:**
- None.

**Recommended Fix:**
Implement a validation check for CSV files similar to `validate_xlsx_upload`. Limit CSV uploads to a reasonable size (e.g., 5MB - 10MB) before handing them off to Pandas.

**Mapping:**
- OWASP: A04:2021 – Insecure Design
- CWE: CWE-400 (Uncontrolled Resource Consumption)


### 3. Formula Injection (CSV / Excel Injection) in Workbook Writes
- **Severity:** High
- **Confidence:** High (Confirmed by source code review showing direct `sheet.cell().value` writes from user input).
- **Business Asset:** End-user Client Security (Admin/Manager endpoints).
- **Likelihood:** Medium
- **Impact:** High (Client-side RCE or data exfiltration when opening the generated files).
- **Verification Method:** Code Review
- **Evidence Quality:** Strong

**Evidence:**
In `core/btpl.py`:
```python
def clean(val):
    if val == "" or val is None:
        return None
    if isinstance(val, str):
        val_strip = val.strip()
        if val_strip == "":
            return None
        return val_strip
    return val

def write_val(key, val):
    col = mapping.get(key)
    if col is not None:
        sheet.cell(row=row, column=col).value = clean(val)

write_val('name', row_data['name'])
write_val('address', row_data['address'])
```
Similar patterns exist in `core/ftl.py` and `core/cof.py`.

**Why this is a Vulnerability:**
When user-supplied input (like `name` or `address` from a web form) begins with characters like `=`, `+`, `-`, or `@`, Excel treats the cell content as a formula. If an attacker submits a payload like `=1+cmd|' /C calc'!A0`, it is written exactly as such into the `.xlsx` file. When an administrator downloads the file and opens it in Excel, the formula executes, potentially launching executables or performing unauthorized actions on the administrator's machine.

**Counter Argument (Pass 2 Challenge):**
*Isn't this an Excel problem? Why fix it in the application?*
While it exploits Excel functionality, it is the application's responsibility to neutralize untrusted data before injecting it into a context (a spreadsheet) where it becomes executable code. Modern frameworks recommend prefixing formula-starting characters with a single quote (`'`) to force Excel to treat them as plain text.

**Attack Preconditions:**
- The attacker must have permissions to submit data to the BTPL, FTL, or COF modules.
- A higher-privileged user (e.g., manager) must download and open the resulting Excel file.

**Exploitation Scenario:**
1. A malicious employee enters `=cmd|' /C calc'!A0` as the Consignee Name in the FTL form.
2. The server writes this payload into the FTL Master Workbook.
3. The Finance Manager downloads the FTL Master Workbook to review shipments.
4. Upon opening, Excel asks to update links/run formulas. The manager clicks "Yes".
5. The command executes, compromising the manager's machine.

**Existing Mitigations:**
- The `clean()` function strips whitespace but does not neutralize formula characters.

**Recommended Fix:**
In `clean()`, check if the string begins with `=`, `+`, `-`, or `@`. If it does, prepend a single apostrophe (`'`) to force Excel to evaluate the cell as literal text rather than a formula.

**Mapping:**
- OWASP: A03:2021 – Injection
- CWE: CWE-1236 (Improper Neutralization of Formula Elements in a CSV File)


### 4. Data Integrity Loss via Concurrent Workbook Modifications
- **Severity:** Medium
- **Confidence:** High (Confirmed by source code review; missing locks in multiple modules).
- **Business Asset:** Data Integrity of Master Workbooks.
- **Likelihood:** High
- **Impact:** Medium (Data corruption or lost updates).
- **Verification Method:** Code Review
- **Evidence Quality:** Strong

**Evidence:**
In `core/views/btpl.py`:
```python
if action == 'save' and request.method == 'POST':
    ...
    btpl_logic.add_btpl_shipment(file_path, row_data, sheet_name=sheet_name)
```
In `core/btpl.py`:
```python
def add_btpl_shipment(file_path, row_data, sheet_name='JUN 26'):
    wb = openpyxl.load_workbook(file_path)
    # ... modifications ...
    wb.save(file_path)
```
This is also true for `core/ftl.py` and `core/attendance.py`.

**Why this is a Vulnerability:**
The application uses the local filesystem as a shared database. `core/cof.py` correctly implements an OS-level file lock (`workbook_lock()`) to prevent race conditions. However, `btpl.py`, `ftl.py`, and `attendance.py` do not. If two users simultaneously submit modifications, both Django worker threads will open the file, modify it in memory, and save it. The last one to save wins, silently overwriting the other user's changes.

**Counter Argument (Pass 2 Challenge):**
*The application cache might mitigate this?*
No. The cache in `btpl.py` is strictly for *reading* data to display previews quickly. `openpyxl.save()` still writes directly to disk, and there is no locking mechanism preventing overlapping disk writes.

**Attack Preconditions:**
- Two requests must overlap in execution time. (Does not require malicious intent; standard usage under load will trigger this).

**Exploitation Scenario:**
1. User A submits an update to BTPL Row 10. Thread 1 loads `BTPL_Shipments.xlsx` into memory.
2. User B submits an update to BTPL Row 11. Thread 2 loads the same `BTPL_Shipments.xlsx` into memory.
3. Thread 1 saves the workbook containing Row 10 modifications.
4. Thread 2 saves the workbook containing Row 11 modifications (which lacks Row 10's modifications).
5. User A's changes are lost forever.

**Existing Mitigations:**
- None for BTPL, FTL, or Attendance. (COF correctly uses `workbook_lock`).

**Recommended Fix:**
Extract the `workbook_lock` context manager from `core/cof.py` and apply it to all workbook modification endpoints in `btpl.py`, `ftl.py`, and `attendance.py`.

**Mapping:**
- OWASP: A04:2021 – Insecure Design
- CWE: CWE-362 (Concurrent Execution using Shared Resource with Improper Synchronization ('Race Condition'))


---

## Evaluated False Positives

### 1. XML External Entity (XXE) / Billion Laughs Attack via `openpyxl`
- **Initial Concern:** Excel files are XML. Parsing them with `openpyxl` might expose the server to XXE (reading local files) or Billion Laughs (XML entity expansion DoS).
- **Analysis:** A review of `requirements.txt` reveals that `defusedxml` is installed. The `openpyxl` library explicitly checks for `defusedxml` on import and automatically switches to it if present. `defusedxml` completely disables external entity resolution and protects against entity expansion attacks out of the box.
- **Conclusion:** **Safe**.

### 2. Path Traversal / Header Injection via `original_name` in Uploaded Files
- **Initial Concern:** Models like `CofWorkbook` store `original_name = upload.name` based on user input. The file download views inject this into the `Content-Disposition` HTTP header (`response['Content-Disposition'] = f'attachment; filename="{filename}"'`).
- **Analysis:** While `original_name` could contain malicious characters (e.g., `../../` or CRLF sequences), Django's `FileResponse` properly escapes and quotes the filename parameter in accordance with RFC 5987. Furthermore, Django templates auto-escape the value when rendering it in the UI, neutralizing Stored XSS vectors. The actual file storage path is handled securely by Django's `FileField` Storage backend, stripping traversal characters.
- **Conclusion:** **Safe**.
