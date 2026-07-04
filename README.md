# EcoFleetExpress

Internal logistics and workforce management portal for EcoFleetExpress.
Built with Django and openpyxl, this application handles employee attendance, salary calculation, FTL trip tracking, BTPL distribution routing, and COF generation.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Optional: Nginx, Gunicorn/uWSGI (for production)

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd EcoFleetExpress
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Configure the environment:**
   Copy `.env.example` to `.env` and fill in the required variables (especially `DATABASE_URL` pointing to your local Postgres, `DJANGO_SECRET_KEY`, and `ECOFLEET_BOOTSTRAP_PASSWORD`).
   ```bash
   cp .env.example .env
   ```

4. **Initialize the database:**
   Ensure your local PostgreSQL service is running and the database specified in `DATABASE_URL` exists.
   ```bash
   python manage.py migrate
   ```

5. **Create initial admin users:**
   ```bash
   python manage.py setup_users
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## Key Features

- **Attendance & Payroll:** Parse monthly Excel attendance sheets to generate accurate salary calculations based on adjustable configurations.
- **FTL Tracking:** Full-Truck-Load trip metric tracking.
- **BTPL Tracking:** CV distribution and payment calculations.
- **COF Letter Generator:** Automated docx letterhead creation for drivers.
- **Operations Center (Observability):** A dynamic dashboard providing live PostgreSQL size tracking, media storage utilization, backup health analysis, recent event timelines, and micro-metrics for all business modules.
- **Automated Backups:** Scheduled via Celery (`core/management/commands/backup_database.py`) supporting both SQLite and PostgreSQL.

## Architecture & Reliability

- **Workbook Integrity:** To prevent corruption during concurrent uploads or edits, the application uses an atomic save pattern and file-based locking (`core/workbook/locking.py`).
- **Database Atomicity:** View operations that modify which workbook is "active" are scoped with `transaction.atomic()` to guarantee consistency.
- **Security:** CSRF trusted origins configured properly, Sentry integration for monitoring, `django-axes` for brute-force protection, and `django-csp` enforcing strict Report-Only Content Security Policy with nonces.
- **Knowledge Graph:** Uses Graphify (`graphify update .`) to maintain a persistent architectural knowledge graph (`graphify-out/`).
