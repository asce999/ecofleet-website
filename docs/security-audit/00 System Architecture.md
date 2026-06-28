# 00 Project Understanding

## Executive Summary
EcoFleetExpress is a monolithic Django application designed to automate and manage logistics and employee operations. It provides an employee portal with various automation tools such as COF generation, Morning Reports, Pendency Reports, and BTPL/FTL Shipment tracking. The application also manages employee attendance and salary calculations based on uploaded Excel workbooks.

## Architecture
- **Framework**: Django 6.0.6 (Monolithic)
- **Database**: SQLite (`db.sqlite3`)
- **App Structure**: The main application logic resides in a single Django app named `core`.
- **Media Serving**: Protected media files are served through a custom view `protected_media` which enforces staff authentication and supports Nginx `X-Accel-Redirect` for performance.
- **Monitoring/Observability**: Integrated with Sentry for error tracking and APM, plus a custom Operations Center dashboard that polls internal provider classes for system health.

## Directory Overview
- `core/`: Main Django application containing models, views, forms, and business logic.
  - `operations/`: Contains the Health Providers for the operations dashboard.
  - `views/`: Contains all controller logic separated into files like `auth.py`, `attendance.py`, `btpl.py`, etc.
  - `cof_assets/`: Static assets used for generating COF documents (e.g., word templates).
- `ecofleet/`: Django project settings and root URL configuration.
- `media/`: Uploaded and generated files (workbooks, output reports), protected from public access.
- `static/` / `staticfiles/`: Static assets.
- `logs/`: Application, error, and security logs configured with rotation.

## Feature Modules
- **COF Generator**: Generates documents (Word/Excel) based on an uploaded COF workbook.
- **Morning Report**: Generates morning operational reports.
- **Pendency Report**: Tracks pending operations.
- **Previous Month Update**: Updates records for the previous month.
- **BTPL Sheet**: Tracks BTPL shipments via workbook uploads.
- **FTL Tracker**: Tracks Full Truckload (FTL) shipments.
- **Attendance & Salary**: Processes employee attendance workbooks and calculates salaries based on configurable rates.

## Provider Hierarchy
The application features a health checking system under `core.operations.providers`:
- `BaseProvider`: The root interface that standardizes health checks and catches exceptions to return fallback "CRITICAL" states.
- Specific providers include `ActivityProvider`, `AttendanceProvider`, `BackupsProvider`, `BusinessProvider`, `COFProvider`, `DatabaseProvider`, `FTLProvider`, `PerformanceProvider`, `SalaryProvider`, `SecurityProvider`, `StorageProvider`, `SystemProvider`.
These are used by the Operations Center to monitor the system state.

## Workbook Flow
Most operational tasks are driven by Excel workbooks.
1. Users upload Excel files (e.g., Attendance, BTPL, FTL) via forms in the employee portal.
2. The uploaded file is saved via its respective model (e.g., `AttendanceWorkbook`, `BtplWorkbook`).
3. Only one workbook of a type is considered "active" at a time (`is_active=True`).
4. Operations (like salary calculation) read from the active workbook.

## Upload Flow
1. A staff user accesses a specific tool (e.g., Attendance Settings).
2. They upload an Excel file via a Django form (e.g., `AttendanceWorkbookUploadForm`).
3. The form validates the file.
4. The view creates a database record pointing to the file and sets it as the active workbook, demoting previous ones.
5. The file is saved in the `media/` directory.

## Authentication Flow
- Handled by `core.views.portal_auth.portal_login`.
- Uses Django's built-in `AuthenticationForm`.
- Successful login requires the user to have `is_staff=True`.
- Protected against brute-force attacks via the `django-axes` package.
- Non-staff users are rejected even with valid credentials.

## Authorization Flow
- Access to the employee portal is strictly controlled by `@staff_required`.
- Fine-grained authorization is handled by the `UserProfile` model, which extends the Django `User` model.
- `UserProfile` contains boolean flags (`can_use_cof`, `can_use_morning`, etc.) dictating access to specific tools.
- `UserProfile` also assigns a `role` (default 'Employee').

## Data Flow
- **Input**: Forms (file uploads, tool triggers, salary overrides).
- **Processing**: Business logic modules in `core` (e.g., `core.attendance`, `core.btpl`) process the files.
- **Tracking**: Every tool execution is logged in the `ToolRun` model.
- **Output**: Output files (e.g., generated reports) are linked to a `ToolRun` via the `ToolRunFile` model and saved to `media/tool_outputs/`.

## Report Generation Flow
1. User triggers a report generation via a portal view.
2. The view typically instantiates a tool function or class.
3. A `ToolRun` record is created to audit the execution.
4. The tool reads data from the database or the active workbook (e.g., via `openpyxl`).
5. Processed data is formatted into an output file (Excel or Word document).
6. The output file is saved as a `ToolRunFile`.
7. The view returns a success page or triggers a download.

## Database Overview
- **Engine**: SQLite (`db.sqlite3`) with WAL journal mode enabled.
- **Key Models**:
  - `Pincode`: Stores pincode data (ODA/Non-ODA).
  - `ToolRun` & `ToolRunFile`: Audit logs and generated files.
  - `*Workbook` Models (`CofWorkbook`, `BtplWorkbook`, `AttendanceWorkbook`, `FtlWorkbook`): Track uploaded excel files.
  - `SalaryConfig` (Singleton) & `EmployeeSalaryOverride`: Global payroll settings and employee-specific overrides.
  - `UserProfile`: Extended user permissions.
  - `SystemEvent`: Operational and security audit trail.

## Entry Points
1. **Public Site**: `/` (Home, Services, Contact, About, Privacy).
2. **Employee Portal**: `/portal/` (Dashboard and tools).
3. **Django Admin**: `/efe-internal-2026/` (Administrative data management).
4. **Protected Media**: `/media/` (Served via custom view).
5. **Observability**: `/health/`, `/sentry-debug/`, `/portal/operations-center/`.

## APIs
- The application primarily uses server-rendered templates.
- Internal API endpoints exist for portal AJAX interactions:
  - `/portal/btpl/api/`
  - `/portal/ftl/api/`

## Middleware
- `axes.middleware.AxesMiddleware`: Brute force protection.
- `whitenoise.middleware.WhiteNoiseMiddleware`: Static file serving.
- `csp.middleware.CSPMiddleware`: Content Security Policy injection.
- `core.middleware.RequestIDMiddleware`: Injects a unique request ID for tracing.
- `core.middleware.PerformanceMiddleware`: Tracks request latency and metrics.
- Standard Django security, session, CSRF, and auth middlewares.

## Third Party Services
- **Sentry**: Application monitoring, error tracking, and APM.
- No other external API services are evident from the initial architecture scan; most logic is file-based processing.

## Trust Boundaries
- **Public vs. Authenticated**: The entire `/portal/` and `/media/` paths are protected and require a staff session.
- **Media Access**: Static web server (Nginx) is blocked from directly serving `/media/`. The Django app authorizes requests and uses `X-Accel-Redirect` to delegate serving back to Nginx.
- **Uploads**: Excel files are uploaded by authenticated staff. These files cross the trust boundary when parsed by the server (e.g., openpyxl).

## Attack Surface Overview
- **Authentication Forms**: Brute-force/credential stuffing (mitigated by `django-axes`).
- **File Uploads**: The application heavily relies on processing Excel workbooks. Malicious files could exploit vulnerabilities in parsing libraries (e.g., XML External Entity injection in Excel).
- **Session Management**: Handled by Django standard libraries.
- **Authorization Bypass**: The custom permission logic in `UserProfile` could be misconfigured.
- **Information Disclosure**: Tracebacks in `SystemEvent` or verbose logging, or unprotected files in `media/`.
- **Cross-Site Scripting (XSS)**: Reflected/Stored XSS in user input. Mitigated partially by CSP, although `'unsafe-inline'` is currently allowed for styles and scripts.

## Important Notes
- The application uses `'unsafe-inline'` for scripts and styles in the CSP due to dependencies like Chart.js, which degrades XSS protections (noted as a TODO in `settings.py`).
- It heavily relies on synchronous file parsing (Excel), which could be a denial-of-service vector if large files are uploaded.
- SQLite is used as the database. While WAL mode is enabled, concurrent high-volume writes could still cause locking issues.
- The `SystemEvent` and `ToolRun` models provide a robust internal audit trail for operations.
