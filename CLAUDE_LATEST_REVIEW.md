# EcoFleet Express — Latest Engineering Review, Flaw Register & Safe-Fix Roadmap

**Date:** 2026-06-30
**Reviewer role:** Staff / Principal Engineer
**Baseline:** Reviewed against commit `763fb42` ("Migrate to PostgreSQL and Implement Shipment Domain"), the current `docs/` corpus, and the Graphify graph (now reflects the Shipment domain).
**Method:** Direct source reading. Every flaw below carries a `file:line` citation verified against the working tree.

> **How to read this document**
> - Each flaw has: **What / Evidence / Why it matters / Exact fix (with code) / Safe-rollout note.**
> - The **Master Roadmap** at the end sequences every fix so that nothing lands before its prerequisites, and no fix can corrupt live data or break a working flow.
> - Three items are **owner-blocked** (Shipment Tracking API, Contact form, Production hosting). Those are called out explicitly with "what to prepare *now* so you're ready the moment details arrive."

---

## 0. Context that shapes this review

Three things are **deliberately not yet built** and are waiting on the project owner. They are **not** counted as flaws — but the roadmap is sequenced around them:

1. **Shipment Tracking API** — pending official spec from the owner. *Do not build endpoints on guesses.* What we **can** do now is make the data layer API-ready (see F-04).
2. **Contact form functionality** — pending requirements (where do messages go? email? CRM? ticket?). Currently the page is **static only** (`core/views/public.py:14-15` renders the template with no POST handling). See F-15 for the secure skeleton to drop in the moment requirements arrive.
3. **Production deployment** — the target domain (`ecofleetexpress.com`) currently hosts the **old site built and operated by a third party, SVP Infotech**. This is the single highest-risk operational item and has its own section (§Deployment Roadmap).

---

## 1. Flaw Register

Severity legend: **P0** = fix immediately (live defect / data integrity) · **P1** = fix before the next milestone · **P2** = scheduled hardening · **P3** = cleanup / nice-to-have.

| ID | Severity | Title | Status vs last review |
|----|----------|-------|-----------------------|
| F-01 | **P0** | `NameError`/HTTP 500 on FTL "edit row" path | **New regression** |
| F-02 | **P0** | Shadow importer is not idempotent (duplicate shipments) | **New** |
| F-03 | **P1** | "PostgreSQL" is a misnomer — still SQLite, no driver | **New** |
| F-04 | **P1** | Excel is still the operational system of record | Carried (C-1) — now scaffolded |
| F-05 | **P1** | ~70% duplication across tool modules + fragile formula evaluator | Carried (H-1/H-2) |
| F-06 | **P2** | CSP allows `'unsafe-inline'` (script + style) | Carried (M-1) |
| F-07 | **P2** | `PerformanceMiddleware` lost-update race + per-request file I/O | Carried (M-2) |
| F-08 | **P2** | `request_id` is dead; audit trail has gaps | Carried (M-3) |
| F-09 | **P2** | Permissions = boolean spray + `'Director'` magic string | Carried (M-5) |
| F-10 | **P2** | Importer runs in a raw fire-and-forget `threading.Thread` | New |
| F-11 | **P3** | Dead code (`ExcelExporter`, unused flags) + bare `except:` | New |
| F-12 | **P3** | Default-data fallback points at gitignored `efe_data/` | Carried (L-1) |
| F-13 | **P3** | Workbook lock is filesystem-local; readers take no lock | Carried residual (H-3) |
| F-14 | **P3** | `AttendanceRecord.driver` conflates driver vs employee | New |
| F-15 | — | Contact form is static-only (owner-blocked) | Pending feature |
| F-16 | **P2** | Single-node substrate ceiling (SQLite + FileBasedCache + FS lock) | Carried |

---

### F-01 — `NameError` → HTTP 500 on the FTL "edit row" path · **P0**

**What.** The FTL JSON API's `get_row` action formats date cells using the `datetime` module, but `datetime` is never imported in that view file.

**Evidence.** `core/views/ftl.py:95`:
```python
if isinstance(val, (datetime.datetime, datetime.date)):
```
The file's imports end at line 16 and contain no `import datetime`.

**Why it matters.** Any user who opens an existing FTL row for editing where `booking_date`, `etd`, or `delivery_date` is populated triggers `NameError: name 'datetime' is not defined` → HTTP 500. This is on a primary user flow and is the exact same defect class as the previously-fixed `messages` `NameError` (C-2) — which means this branch has no test.

**Exact fix.** Add the import at the top of `core/views/ftl.py`:
```python
import datetime
```
Then add a regression test asserting `get_row` returns 200 with ISO-formatted dates for a row that has a real date value:
```python
# tests/unit/core/test_ftl_views.py
def test_get_row_with_date_does_not_500(self):
    # seed an FTL workbook whose row 2 has a booking_date
    resp = self.client.get(reverse('ftl_api'), {'action': 'get_row', 'row': 2})
    self.assertEqual(resp.status_code, 200)
    self.assertRegex(resp.json()['row_data']['booking_date'], r'\d{4}-\d{2}-\d{2}')
```

**Safe-rollout note.** Zero risk — additive import + new test. Ship on its own tiny branch today.

---

### F-02 — Shadow importer is not idempotent (duplicate shipments on re-import) · **P0**

**What.** `ExcelImporter._process_ftl_row` creates a new `Shipment` per row with no natural key or dedupe. Re-uploading the same FTL workbook (or re-running the import) silently doubles the data.

**Evidence.** `core/importers/excel_importer.py:104-117` — bare `Shipment.objects.create(...)`; the upload hook fires the importer on every upload (`core/views/ftl.py:281-291`). Vehicles are `get_or_create`'d (line 88) but shipments are not.

**Why it matters.** Today this is masked because `use_database_reads`/`use_database_exports` are off — nothing reads the rows back. But the **moment** dual-read is enabled, every re-upload inflates counts, analytics, and (eventually) the Tracking API. Silent data-integrity bugs in a write-only shadow store are the worst kind: invisible until cutover.

**Exact fix.** Give `Shipment` a stable natural key derived from the source row (FTL has LR Number + dispatch date as a practical key) and upsert instead of insert:

1. Add a deterministic key field + uniqueness:
```python
# models.py — on Shipment
source_key = models.CharField(max_length=200, blank=True, db_index=True)

class Meta:
    ordering = ['-dispatch_date']
    constraints = [
        models.UniqueConstraint(
            fields=['shipment_type', 'source_key'],
            condition=~Q(source_key=''),
            name='unique_shipment_source_key',
        )
    ]
```
2. In the importer, compute the key and `update_or_create`:
```python
lr = str(get_val('lr_number') or '').strip().upper()
key = f"{lr}|{booking_date.isoformat() if booking_date else ''}"
shipment, _ = Shipment.objects.update_or_create(
    shipment_type='FTL', source_key=key,
    defaults=dict(origin=str(origin), destination=str(destination),
                  dispatch_date=booking_date, vehicle=vehicle_obj, metadata={...}),
)
# only append a status if it changed, to avoid status-log bloat
ShipmentStatus.objects.get_or_create(shipment=shipment, status=status_val)
```
3. Rows with no usable key (no LR, no date) should be counted as `failed` with an `ImportErrorRecord`, **not** inserted as anonymous duplicates.

**Safe-rollout note.** This only touches the shadow store (flags off), so it cannot affect live Excel flows. Land it **before** ever flipping `use_database_reads`. Run the importer twice against the same file in a test and assert the row count is stable (`core/tests/test_importers.py` is the right home).

---

### F-03 — "PostgreSQL" is a misnomer; the app still runs on SQLite · **P1**

**What.** The commit and several docs imply a PostgreSQL cutover. The running configuration is still SQLite, and there is no Postgres driver in `requirements.txt`.

**Evidence.** `ecofleet/settings.py:137` → `'ENGINE': 'django.db.backends.sqlite3'`; `requirements.txt` lists no `psycopg`/`psycopg2` (the only new dependency is `psutil`, for the lock). The new domain models are DB-agnostic, so they run on SQLite unchanged.

**Why it matters.** Anyone reading the commit history will believe production is Postgres-ready. It is not. The `PRAGMA journal_mode=WAL` (`settings.py:140`) is a sensible SQLite concurrency tweak, but SQLite remains a single-writer, single-node store — incompatible with the multi-worker production the roadmap targets.

**Exact fix.** The team has decided to move to PostgreSQL now, so this is no longer just a wording correction — it is a **first-class, prioritized migration (Sprint 2)**. The full step-by-step is in **§3 — PostgreSQL Migration Playbook**. In short: make the engine env-driven, stand up Postgres, migrate the existing SQLite data (`dumpdata`→`loaddata`), fix the SQLite-only backup command, and verify row counts. Correct the docs in the same pass so history stops implying it already happened.

**Safe-rollout note.** Two non-obvious dependencies for *this* repo: (1) `core/management/commands/backup_database.py` uses the `sqlite3` backup API and **will break on Postgres** — it must be updated in the same sprint; (2) the `OPTIONS` block in `settings.py:139-141` (`timeout`, `PRAGMA journal_mode=WAL`) is **SQLite-only** and will error under psycopg, so the env-driven config must not pass it to Postgres. Keep `db.sqlite3` untouched after the move — switching back is an env-var flip until SQLite is formally decommissioned.

---

### F-04 — Excel is still the operational system of record · **P1** (carried C-1, now scaffolded)

**What.** The Shipment domain (`models.py:330-541`) is good groundwork, but it is shadow-only: all three `MigrationFeatureFlags` default `False`, only **FTL** has an importer, the path is **write-only** (`use_database_reads` is never referenced), and `ExcelExporter` is never called. The live system of record is still the spreadsheet, mutated in place via `openpyxl`.

**Evidence.** `core/models.py:336-347` (flags default false); importer wired only at `core/views/ftl.py:281`; `grep` shows `use_database_reads`/`ExcelExporter` have **zero** call sites.

**Why it matters.** Every downstream roadmap item (Tracking API, Analytics, Fleet) needs queryable relational data. The scaffold is the correct first slice, but C-1 is not closed until reads come from the DB.

**Exact fix — staged "strangler-fig" cutover, FTL first:**
1. **Idempotent import (F-02)** — prerequisite. Without it, dual-read shows doubled data.
2. **Reconciliation command** — a read-only management command that parses the active FTL workbook and the DB and reports diffs:
```python
# core/management/commands/reconcile_ftl.py — count + field-level diff, exits non-zero on mismatch
```
3. **Dual-read behind the flag** — in `get_active_ftl_workbook` / the FTL page view, branch on `MigrationFeatureFlags.get_solo().use_database_reads` to read from `Shipment` instead of the sheet, rendering the **same** template context. Keep Excel as the fallback.
4. **Soak** with reconciliation green for a defined period, then make DB authoritative and Excel export-only (wire `ExcelExporter` into `ftl_download`).
5. **Repeat for BTPL**, then Attendance.

**Safe-rollout note.** The flag is the safety valve: every step is reversible by flipping it off. Never advance a stage while reconciliation reports a diff. Do **not** start BTPL/Attendance importers until FTL is fully cut over — one domain at a time bounds blast radius.

---

### F-05 — ~70% duplication across tool modules + fragile formula evaluator · **P1** (carried H-1/H-2)

**What.** `btpl.py`, `ftl.py`, `attendance.py`, `cof.py` re-implement near-identical column-mapping / row-finding / read / write / preview / pagination / mtime-cache machinery. A hand-rolled `evaluate_cell` parses a fragile subset of spreadsheet formulas.

**Evidence.** Compare `core/btpl.py:29-55` vs `core/ftl.py` column mapping; `evaluate_cell` in `core/btpl.py` (string-splits `=A1*B1`); `core/ftl.py`'s version returns the raw formula string.

**Why it matters.** Every bug fix must be applied 2–4 times; financial values flow through a partial formula engine with no test coverage.

**Exact fix.** This is **Phase 4 (Workbook Simplification)** in the roadmap and should be done *after* F-04, scoped only to whatever remains as import/export. Extract a `WorkbookGrid`/`SheetTable` abstraction parameterized by a `HEADER_MAP`, exposing `map_columns`, `find_next_empty_row`, `read_row`, `write_row`, `clear_row`, `paginated_preview`, `cached_raw`. For formulas: prefer **writing computed values to the DB at write-time** (natural under F-04) so read-time evaluation disappears; if formulas must stay in Excel, load with `data_only=True`.

**Safe-rollout note.** **Do not refactor before F-04 decides what survives** — collapsing four modules that are about to become DB tables is wasted, risky churn. Gate this work behind golden-file round-trip tests (read sheet → write sheet → assert byte/values stable) so the refactor is provably behavior-preserving.

---

### F-06 — CSP allows `'unsafe-inline'` for script and style · **P2** (carried M-1)

**What.** `CSP_SCRIPT_SRC` and `CSP_STYLE_SRC` both include `'unsafe-inline'`, already flagged by an in-code `TODO(SECURITY)`.

**Evidence.** `ecofleet/settings.py:113-114` (and the TODO at `110-112`).

**Why it matters.** It defeats CSP as a second line of defense against injected-script XSS — the weakest link in an otherwise strong XSS posture.

**Exact fix.** Adopt per-request **nonces** (django-csp supports them) and move inline `<script>`/`style` into static files or nonce-tagged blocks:
```python
# settings.py
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'script-src': ["'self'", "https://cdn.jsdelivr.net"],
        'style-src': ["'self'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net"],
    }
}
CSP_INCLUDE_NONCE_IN = ['script-src', 'style-src']
```
```django
<script nonce="{{ request.csp_nonce }}"> ... </script>
```
Also add **Subresource Integrity (SRI)** to the pinned CDN Chart.js tag.

**Safe-rollout note.** Roll out behind **`Content-Security-Policy-Report-Only`** first, watch the violation reports, fix every inline block, then enforce. Never drop `unsafe-inline` and enforce in the same deploy — you will white-screen the dashboard if one inline block is missed.

---

### F-07 — `PerformanceMiddleware` lost-update race + per-request file I/O · **P2** (carried M-2)

**What.** Every non-static request does a read-modify-write of a single cache key with `timeout=None`. Concurrent requests clobber each other's updates; the metrics drift and the middleware adds a file read+write to every request's latency.

**Evidence.** `core/middleware.py:18-46` — `cache.get('performance_metrics', ...)` → mutate → `cache.set(..., timeout=None)` against `FileBasedCache`.

**Why it matters.** The performance numbers shown in the Operations Center are themselves unreliable, and the middleware adds the very latency it measures. Under multiple workers (production) it gets worse.

**Exact fix.** Short term: bound the work and stop storing raw `request.path` (store the resolved view name) — or guard the read-modify-write. Proper fix (ties into Phase 5/Redis): move to atomic counters (`cache.incr` on Redis) or, better, a real metrics exporter (`django-prometheus` + `/metrics`).

**Safe-rollout note.** Low risk — this code already degrades gracefully. Defer the real fix to Phase 5 when Redis lands; until then, the one-line "store view name not path" change removes the unbounded-key concern with no behavior change.

---

### F-08 — `request_id` is dead; audit trail has gaps · **P2** (carried M-3)

**What.** `SystemEvent.request_id` exists but nothing populates it; logins, lockouts, permission changes, and workbook activations aren't recorded as `SystemEvent`s, so logs ↔ events ↔ Sentry can't be correlated.

**Evidence.** `core/models.py:318` (field exists); the only custom middleware is `PerformanceMiddleware` (`settings.py:104`), which never sets a request id.

**Why it matters.** Incident reconstruction across the workflow chain is hard; audit coverage is partial.

**Exact fix.** Add a `RequestIDMiddleware` that mints a UUID per request, injects it into a logging filter and into `SystemEvent.request_id`, and emit `SystemEvent`s on: login success/failure, axes lockout (`user_locked_out` signal), permission change, and workbook activation.

**Safe-rollout note.** Purely additive (new middleware + new event writes). Add the middleware **last** in `MIDDLEWARE` and make event-writing best-effort (wrapped in try/except) so an audit-write failure can never break a user request.

---

### F-09 — Permissions are a boolean spray + `'Director'` magic string · **P2** (carried M-5)

**What.** Seven `can_use_*` booleans on `UserProfile` plus a free-text `role` with `'Director'` hardcoded in logic. Every new tool needs a migration + column; roles are stringly-typed.

**Evidence.** `core/models.py:285-292`; `'Director'` checks at `core/models.py:25` and `core/decorators.py:64`.

**Why it matters.** Adding Fleet/Driver/Analytics means schema churn and scattered magic-string checks.

**Exact fix.** Migrate to Django Groups/Permissions (or a `Role`→permissions table); replace `'Director'` with a constant/enum (`Role.DIRECTOR`). Keep the `can_use_*` accessors as a thin compatibility shim during transition.

**Safe-rollout note.** Not blocking until the permission surface grows — do it **before** Fleet Management (Phase 8), not now. When you do, dual-write (booleans **and** groups) for one release so you can roll back without re-provisioning users.

---

### F-10 — Importer runs in a raw fire-and-forget `threading.Thread` · **P2**

**What.** The shadow importer is launched in a bare thread from the request handler.

**Evidence.** `core/views/ftl.py:288-291` (`threading.Thread(target=...).start()`).

**Why it matters.** Thread death is silent (only row-level errors land in `ImportErrorRecord`); under a production WSGI server the worker can be recycled mid-import; there's no retry, no visibility, no backpressure. Acceptable for a shadow trickle, **not** for real import volume.

**Exact fix.** Replace with **Celery + Redis** (Phase 5 deliverable). Until then, keep the thread but: wrap the whole `process_ftl_workbook` body so any fatal error marks the `ImportJob` `FAILED` (it already does — keep it), and surface job status in the UI so a silent death is visible.

**Safe-rollout note.** Don't introduce Celery as a one-off; bring it in as part of the Phase 5 infra step so broker, worker, and monitoring arrive together. Swapping `thread.start()` for `task.delay()` is then a one-line change.

---

### F-11 — Dead code + bare `except:` in the importer · **P3**

**What.** `ExcelExporter` and the `use_database_reads`/`use_database_exports` flags are defined but never referenced; the importer has a bare `except:`.

**Evidence.** `grep` shows no call sites for `ExcelExporter`/`export_ftl_shipments`; bare `except:` at `core/importers/excel_importer.py:101`.

**Why it matters.** Scaffolding committed ahead of use reads as "live" to the next reader; bare `except:` swallows `KeyboardInterrupt`/`SystemExit` and hides parse bugs.

**Exact fix.** Add `# TODO(phase-3): wired when dual-read/export lands` next to the unused symbols (or keep them on a feature branch); change `except:` → `except (ValueError, TypeError, dateutil.parser.ParserError):` with the error recorded.

**Safe-rollout note.** Trivial, no behavior change. Bundle with F-02 since it's the same file.

---

### F-12 — Default-data fallback points at gitignored `efe_data/` · **P3** (carried L-1)

**What.** When no workbook record exists, code falls back to `BASE_DIR/efe_data/*.xlsx`, but `efe_data/` is gitignored — a clean prod deploy won't have it.

**Evidence.** `core/views/ftl.py:30` (and the BTPL/attendance equivalents).

**Exact fix.** Ship tracked seed templates under `core/<tool>/templates_default/`, or generate empty workbooks on first run via `WorkbookManager`. Point the fallback there.

**Safe-rollout note.** Matters for first-deploy reliability — do it during the deployment-prep phase, before cutover.

---

### F-13 — Workbook lock is filesystem-local; readers take no lock · **P3** (carried residual of H-3)

**What.** The lock is now robust (PID + stale-TTL + dead-PID reclaim) but is a local lock file; it cannot coordinate across multiple app hosts. Readers don't lock.

**Evidence.** `core/workbook/locking.py:33-68`. (Note: `atomic_save_workbook` via `os.replace` already removes the torn-read risk, so reader-locking is no longer urgent.)

**Why it matters.** Only relevant once you run more than one app host (production). Dissolves entirely once F-04 moves writes to DB rows under `transaction.atomic`.

**Exact fix.** No action until multi-host. Then either move the write of record to the DB (preferred, via F-04) or use a Redis-backed lock (`redis-py` `Lock`) shared across hosts.

**Safe-rollout note.** Explicitly deferred. Don't build a distributed file lock — let F-04 retire the problem.

---

### F-14 — `AttendanceRecord.driver` conflates "driver" with "employee" · **P3**

**What.** Attendance/payroll is about employees, but `AttendanceRecord` FKs to `Driver`.

**Evidence.** `core/models.py:486`.

**Why it matters.** Payroll covers office staff too (the salary config has `CV-SUPERVISOR`, `CV-DEO` departments). Modeling all employees as `Driver` will leak into HR/analytics later.

**Exact fix.** Introduce an `Employee` model (or a person/party model) and point `AttendanceRecord`/salary at it; keep `Driver` as a role/specialization. Only needed when the Attendance domain is actually migrated (after FTL/BTPL).

**Safe-rollout note.** Don't rename now — it's shadow/unused. Fix it as the *first* step of the Attendance-domain migration so you never have to migrate attendance rows twice.

---

### F-15 — Contact form is static-only (owner-blocked feature) · pending

**What.** `/contact/` renders a template with no POST handling, no validation, no delivery, no anti-spam.

**Evidence.** `core/views/public.py:14-15`.

**Why it's not a "flaw" yet.** Functionality is intentionally pending the owner's requirements (destination, email vs CRM, fields).

**Prepare now (so it's a 30-minute job when details land).** Have the secure pattern ready:
- A Django `Form` with explicit field validation.
- **CSRF** (Django default) — ensure the template has `{% csrf_token %}`.
- **Anti-spam**: honeypot field + rate limiting (django-axes is already present; or a simple per-IP throttle) + optionally hCaptcha/Turnstile.
- **Delivery** via `django.core.mail.send_mail` using the **already-configured `EMAIL_*` env vars** — but see the Deployment section: **do not send mail from the new app until the domain's MX/SPF/DKIM story is confirmed with SVP Infotech**, or you risk deliverability problems and possibly interfering with existing mail.
- Persist submissions to a `ContactMessage` model so nothing is lost if email fails.

**Safe-rollout note.** Build the model + form + persistence first (no external dependency), wire email last once DNS/mail is confirmed.

---

### F-16 — Single-node substrate ceiling · **P2** (carried)

**What.** SQLite + `FileBasedCache` + filesystem lock all assume one host.

**Evidence.** `settings.py:135-152` (SQLite + FileBasedCache).

**Exact fix.** Phase 5: PostgreSQL + Redis (cache + Celery broker). Covered by F-03/F-07/F-10.

**Safe-rollout note.** This is the explicit gate for multi-worker production; sequence it as one coordinated infra phase, not piecemeal.

---

## 2. Deployment Roadmap — the SVP Infotech / shared-domain situation

This is the highest-risk operational item because **the production domain (`ecofleetexpress.com`) currently serves a live site that a third party (SVP Infotech) built and operates.** A careless cutover can take the company's public presence offline. Treat this as a coordinated migration, not a deploy.

### Stage D0 — Discovery (do this *before* writing any deploy config)
You cannot plan a safe cutover without these answers. Get them from the owner / SVP Infotech in writing:
1. **Who controls the DNS registrar and the authoritative DNS zone?** (registrar login or ability to request record changes)
2. **What is the current TTL on the A/AAAA/CNAME records?** (you'll want it lowered *days* before cutover)
3. **Current hosting**: provider, OS, web server / reverse proxy, how SSL is provisioned and renewed.
4. **Email / MX**: does `ecofleetexpress.com` send/receive mail today? What are the MX/SPF/DKIM/DMARC records? (Critical before the contact form sends mail — F-15.)
5. **Will the new site fully replace the old one, or coexist** (e.g. marketing pages stay, portal is added at a path/subdomain)?
6. **Can SVP Infotech give you a staging subdomain** (e.g. `staging.ecofleetexpress.com`) and/or **a server you control**?
7. **Rollback**: can the old site be restored quickly (image/snapshot) if cutover fails?

> ⚠️ Per the roadmap, hosting specifics are owner/SVP-provided. **Do not assume** provider, OS, proxy, or SSL. Stage D0 is about *resolving* those unknowns.

### Stage D1 — Prepare the app to be deployable anywhere (do now, no blockers)
These are provider-agnostic and safe to do today:
- Add a **production WSGI server** (`gunicorn`) to `requirements.txt`.
- Make config fully env-driven and verify: `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `SECURE_SSL_REDIRECT`, `SENTRY_DSN`, `EMAIL_*`. (Most are already env-read — confirm the new domain is in the lists.)
- Run and fix **`python manage.py check --deploy`** until clean.
- Replace the gitignored `efe_data/` fallback with tracked seed templates (F-12).
- Confirm static files serve via WhiteNoise (already present) under `DEBUG=False`.
- Document a one-command bring-up (README already exists — extend it).

### Stage D2 — Stand up staging on a subdomain
- Deploy to `staging.ecofleetexpress.com` (or a temporary host) **without touching the live apex domain**.
- This is where you exercise PostgreSQL + Redis + Celery (Phase 5) and the F-04 dual-read soak, prod-like, with zero risk to the live site.

### Stage D3 — Pre-cutover checklist (live domain)
- Lower DNS TTL to 300s **at least 48h before** cutover (so rollback propagates fast).
- Provision SSL for the new origin (coordinate with SVP — Let's Encrypt or their cert).
- Final `check --deploy` clean; backups configured and a **restore drill** performed.
- Health check (`/health/`) green; Sentry receiving events; logs writing.
- Confirm MX records are **unchanged** by the cutover (you're moving web, not mail) — or explicitly coordinated if mail moves.
- Written rollback plan: revert the A record to SVP's origin.

### Stage D4 — Cutover
- Repoint the apex A/AAAA (or CNAME) to the new origin during a low-traffic window.
- Monitor: error rate (Sentry), `/health/`, latency, a manual smoke test of every portal tool + the public pages.
- Keep the old site reachable (don't decommission) until the new site is proven for a defined soak window.

### Stage D5 — Post-cutover
- Restore normal DNS TTL.
- Decommission/snapshot the old site only after sign-off.
- Hand over runbook + backup/restore + rollback docs.

---

## 3. PostgreSQL Migration Playbook (SQLite → Postgres)

> The team has decided to shift the database from SQLite to PostgreSQL. This section is the exact, repo-specific procedure. It is sequenced as **Sprint 2** in the Master Roadmap — i.e. **right after the P0 correctness fixes and *before* the FTL dual-read cutover**. Doing it in that order means you migrate the data **once** and run every later reconciliation directly against the real target database.

### Why do it now (not later)
- **The Shipment-domain tables are empty (0 rows today).** Migrating before any shadow data lands means there is nothing to reconcile twice. The longer you wait, the more shadow data you have to move.
- **The dual-read soak (F-04) should run on Postgres**, not on SQLite and then re-validated on Postgres. Migrating first avoids doing that verification work twice.
- The new models already use `UUIDField` PKs and `JSONField` — both are **first-class on Postgres** (UUID and `jsonb`). The codebase has **no raw SQL** and no SQLite-specific query hacks (verified), so the application layer needs essentially no changes.

### What data must survive (current SQLite contents)
| Table | Rows | Notes |
|-------|------|-------|
| `core_pincode` | **21,758** | Serviceability dataset — the big one; must transfer intact |
| `auth_user` / `core_userprofile` | 15 | Accounts + password hashes + permissions — **must preserve** |
| `core_salaryconfig` / `core_employeesalaryoverride` | 1 / 20 | Tuned payroll values — irreplaceable |
| `core_toolrun` / `core_toolrunfile` | 81 / 111 | Audit history + output file pointers |
| `core_cofworkbook` / `core_attendanceworkbook` | 5 / 1 | Active-workbook pointers |
| `core_systemevent`, `axes_accesslog` | 4 / 14 | Event/audit logs |
| All Shipment-domain tables | **0** | Nothing to migrate — clean slate |

Total is ~22k rows, dominated by pincodes. **At this scale, Django's `dumpdata`/`loaddata` is the right tool** — `pgloader` or manual SQL is unnecessary complexity.

### Step-by-step

**P2.1 — Dependencies & env-driven settings**
- Add to `requirements.txt`: `psycopg[binary]==3.2.*` and `dj-database-url==2.*`.
- Replace the hardcoded `DATABASES` block (`settings.py:135-152`) with an env-driven one that **only applies the SQLite `OPTIONS` to SQLite**:
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}
# SQLite-only tuning; must NOT be sent to psycopg
if DATABASES['default']['ENGINE'].endswith('sqlite3'):
    DATABASES['default'].setdefault('OPTIONS', {}).update({
        'timeout': 20,
        'init_command': 'PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;',
    })
```
- Dev/prod then differ only by a `DATABASE_URL` env var (e.g. `postgres://user:pass@localhost:5432/ecofleet`). No `DATABASE_URL` set → SQLite, so existing local setups keep working.

**P2.2 — Stand up Postgres (dev/staging first)**
- Run a local Postgres 16 (Docker or native). Create a UTF-8 database (`ENCODING 'UTF8'`) — the pincode city/state strings need it.
- **Do not** touch the SVP-Infotech production hosting yet (that's the Deployment Roadmap, §2). This step is dev + the `staging.ecofleetexpress.com` box.

**P2.3 — Export the current data**
```bash
python manage.py dumpdata \
  --natural-foreign --natural-primary \
  -e contenttypes -e auth.permission -e admin.logentry -e sessions.session \
  --indent 2 -o datadump.json
```
Excluding `contenttypes` and `auth.permission` avoids primary-key clashes with the rows Django auto-creates on a fresh `migrate`; sessions are disposable.

**P2.4 — Build the schema on Postgres & load**
```bash
# with DATABASE_URL pointed at the empty Postgres DB:
python manage.py migrate          # creates the schema fresh
python manage.py loaddata datadump.json
```
`loaddata` correctly resets integer-PK sequences (Pincode, ToolRun, …), so there are no "duplicate key" surprises on the next insert.

**P2.5 — Verify (the guard)**
- Compare row counts table-by-table against the SQLite source (the table above is your checklist). A tiny management command or a `dbshell` `SELECT count(*)` per table is enough.
- Smoke-test the portal against Postgres: log in (proves password hashes migrated), open the pincode finder (proves the 21,758 rows are queryable), open each tool, view the dashboard.
- Run the full Django test suite with `DATABASE_URL` pointed at a Postgres test DB.

**P2.6 — Fix the SQLite-only backup command**
- `core/management/commands/backup_database.py` uses `sqlite3.connect(...)` and the SQLite backup API — it **will fail on Postgres**. Update it to branch on the engine and shell out to `pg_dump` (gzip the output) when on Postgres, keeping the SQLite path for local dev. The backup/restore drill in the deployment checklist (§2, D3) depends on this working.

### Repo-specific gotchas (and why they're already low-risk here)
- **`__iexact` / `__icontains`** (`core/views/portal_views.py:26`, `observability.py:169`) map to Postgres `ILIKE` and behave correctly. The only behavior change to watch: SQLite's default `LIKE`/`=` on text is case-insensitive ASCII, Postgres is case-sensitive — but the codebase uses the explicit `i`-variants where it matters, so no query needs rewriting. (Confirmed: no plain `__exact` string filters relying on fold.)
- **Strict typing.** Postgres rejects values SQLite tolerates (e.g. a malformed date stored as text). The data here is Django-written (Decimals, real dates), so `loaddata` should be clean — but if a row fails to load, that row had bad data worth fixing anyway.
- **`JSONField`** migrates transparently to `jsonb`.
- **No raw SQL / cursors** in the app (verified) — nothing hand-written to port.

### Rollback
Keep `db.sqlite3` on disk and **unmodified**. If anything goes wrong on Postgres, unset `DATABASE_URL` and you are instantly back on the known-good SQLite database. Only decommission SQLite after a defined soak window on Postgres with backups proven.

---

## 4. Master Roadmap — ordered so nothing breaks

The ordering principle: **correctness defects first → move to Postgres once → make the shadow store trustworthy → cut over one domain → only then refactor/scale/feature.** Each step lists its guard (the thing that proves it didn't break anything).

### Sprint 1 — Stop the bleeding (this week, P0)
| Step | Fix | Guard |
|------|-----|-------|
| 1.1 | **F-01** `import datetime` in `views/ftl.py` | New `get_row` regression test green |
| 1.2 | **F-02** idempotent importer (`source_key` + `update_or_create`) | Double-import test → stable row count |
| 1.3 | **F-11** kill bare `except:`, annotate dead scaffold | Importer test still green |

*No flag flips, no schema cutover. Only the shadow store and a one-line view fix change. Fully reversible.*

> **Why correctness before the DB move:** migrating a database that still has a known 500 (F-01) and a non-idempotent importer (F-02) just carries the bugs across. Fix them on SQLite first — it's faster to iterate on — then move a clean app to Postgres.

### Sprint 2 — Shift to PostgreSQL (P1, the new priority) → full procedure in §3
| Step | Fix | Guard |
|------|-----|-------|
| 2.1 | **F-03** deps + env-driven `DATABASES` (SQLite `OPTIONS` gated) | App still boots on SQLite with no `DATABASE_URL` |
| 2.2 | Stand up Postgres on dev + `staging` (UTF-8) | Empty DB reachable |
| 2.3 | `dumpdata` → `migrate` (fresh) → `loaddata` | **Row counts match** the §3 table (esp. 21,758 pincodes, 15 users) |
| 2.4 | Smoke test on Postgres (login, pincode finder, every tool, dashboard) | All green; full test suite passes on PG |
| 2.5 | Fix SQLite-only `backup_database.py` (→ `pg_dump`) | Backup + restore drill succeeds on PG |
| 2.6 | Correct the "Postgres" wording in `docs/` | Docs reviewed |

*Reversible at every step: `db.sqlite3` stays untouched, so unsetting `DATABASE_URL` reverts instantly. Do **not** start Sprint 3 until row counts reconcile and the test suite is green on Postgres.*

### Sprint 3 — Make the DB trustworthy enough to read (P1, on Postgres)
| Step | Fix | Guard |
|------|-----|-------|
| 3.1 | **F-04 step 2** `reconcile_ftl` management command | Reconciliation report runs, diffs visible |
| 3.2 | **F-04 step 3** dual-read behind `use_database_reads` (FTL only) | Same template output sheet vs DB; reconciliation zero-diff |
| 3.3 | Round-trip + golden-file tests for FTL read path | Tests green |

*Flag stays off in prod until 3.1/3.2 are proven on staging. The flag is the rollback. This now runs against Postgres — the real target — so no re-validation later.*

### Sprint 4 — Remaining production infrastructure (Phase 5 / F-16)
| Step | Fix | Guard |
|------|-----|-------|
| 4.1 | **F-07** Redis cache; atomic metrics | Dashboard metrics stable under load test |
| 4.2 | **F-10** Celery + Redis broker; importer → task | Import job visible, retried, monitored |
| 4.3 | **F-08** request-id middleware + audit `SystemEvent`s | Log↔event↔Sentry correlation verified |
| 4.4 | **F-13** retire/relocate file lock (DB writes or Redis lock) | Multi-worker write test |

*Postgres already landed in Sprint 2; this sprint is the rest of the multi-node substrate (Redis + Celery). All proven on staging (D2) before any production cutover.*

### Sprint 5 — Finish the FTL cutover, then BTPL (P1, F-04)
| Step | Fix | Guard |
|------|-----|-------|
| 5.1 | Make DB authoritative for FTL; wire `ExcelExporter` into download | Reconciliation green for full soak window |
| 5.2 | BTPL importer (idempotent from day one) + dual-read | BTPL reconciliation zero-diff |
| 5.3 | Attendance: introduce `Employee` (**F-14**) then migrate | Attendance reconciliation zero-diff |

*One domain at a time. Never start the next domain until the previous is fully authoritative.*

### Sprint 6 — Simplification & hardening (P2, after data is in DB)
| Step | Fix | Guard |
|------|-----|-------|
| 6.1 | **F-05** workbook engine consolidation (Phase 4) | Golden-file round-trip tests prove behavior-preserving |
| 6.2 | **F-06** CSP nonces via Report-Only → enforce | No CSP violations in report mode for a week |
| 6.3 | **F-09** Groups/Permissions + role enum (before Fleet) | Dual-write release; permission tests |
| 6.4 | **F-12** tracked seed templates | First-deploy-from-clean test |

### Owner-blocked tracks (start the moment details arrive)
- **Contact form (F-15)**: build `ContactMessage` model + form + persistence **now** (no blocker); wire email only after Deployment D0/D3 confirms MX/SPF/DKIM.
- **Shipment Tracking API (Phase 6)**: blocked on spec. Prerequisite is F-04 (FTL+BTPL in DB, Sprint 5) + the Sprint 2 Postgres move + Sprint 4 infra (Redis/Celery). When the spec arrives, the data layer is already API-ready; build read endpoints first, behind DRF + auth + rate limiting.
- **Production deployment (Phase 7)**: follow the Deployment Roadmap §2. D0 discovery can start immediately — it's just questions for the owner/SVP.

---

## 5. The one rule that prevents new bugs

**Every flag flip and every cutover step must have a reconciliation guard and a reversible switch.** The Shipment migration is safe precisely because `MigrationFeatureFlags` lets you turn DB reads off instantly. Preserve that property: never make the DB authoritative for a domain while reconciliation shows a diff, and never refactor (F-05) a workbook module before F-04 has decided whether it survives. Correctness fixes (Sprint 1) are the only things that ship without a flag — because they only remove defects, they don't change data flow.

---

*Citations verified against the working tree at commit `763fb42`. No rewrite recommended — this is sequenced, guarded, reversible surgery.*
