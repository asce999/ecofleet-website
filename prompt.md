# EcoFleet Express — Unauthenticated Media File Access Fix

## Context

You are working on a Django web application called **EcoFleet Express** (Python/Django, SQLite, WhiteNoise, deployed behind Nginx). A security audit identified that all uploaded and generated files under `/media/` are served directly by Nginx with no authentication check. Any person who can guess or enumerate a URL like `https://ecofleetexpress.com/media/attendance/attendance_june2026.xlsx` gets the file with no login required.

The fix has two parts:
1. A Django view that checks authentication before streaming the file
2. Nginx configuration that blocks direct `/media/` access and routes requests through Django instead

Do NOT change any model `upload_to` paths, file storage logic, or existing URL patterns outside of what is specified below.

---

## Part 1 — Django: Protected Media View

### Step 1 — Create the protected media view

**File:** `core/views/media.py` (create if it doesn't exist)

```python
import os
from django.http import FileResponse, Http404
from django.conf import settings
from core.decorators import staff_required

@staff_required
def protected_media(request, path):
    """
    Serve media files only to authenticated staff users.
    Uses X-Accel-Redirect if NGINX_ACCEL_REDIRECT is True in settings,
    otherwise streams directly via FileResponse (for local dev).
    """
    full_path = os.path.join(settings.MEDIA_ROOT, path)

    # Prevent path traversal
    media_root = os.path.realpath(settings.MEDIA_ROOT)
    requested = os.path.realpath(full_path)
    if not requested.startswith(media_root):
        raise Http404

    if not os.path.isfile(requested):
        raise Http404

    if getattr(settings, 'NGINX_ACCEL_REDIRECT', False):
        # Let Nginx serve the file efficiently after Django auth check
        response = FileResponse(open(requested, 'rb'))
        response['X-Accel-Redirect'] = '/protected-media/' + path
        response['Content-Type'] = ''  # Let Nginx set this
        return response

    return FileResponse(open(requested, 'rb'))
```

### Step 2 — Register the URL

**File:** `ecofleet/urls.py`

Add this import at the top:
```python
from core.views.media import protected_media
```

Add this URL pattern (place it before any catch-all patterns):
```python
path('media/<path:path>', protected_media, name='protected_media'),
```

Remove or comment out the existing `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` line if present — it is only for development and bypasses auth.

### Step 3 — Add `NGINX_ACCEL_REDIRECT` to settings

**File:** `ecofleet/settings.py`

Add this line near the bottom, controlled by environment variable:
```python
NGINX_ACCEL_REDIRECT = os.environ.get('NGINX_ACCEL_REDIRECT', 'False') == 'True'
```

Set `NGINX_ACCEL_REDIRECT=False` in local `.env` and `NGINX_ACCEL_REDIRECT=True` on the production server.

---

## Part 2 — Nginx Configuration

### Step 4 — Update Nginx site config

**File:** your Nginx site config (e.g. `/etc/nginx/sites-available/ecofleetexpress`)

Make the following changes:

**Remove or disable** any existing block that serves `/media/` directly:
```nginx
# DELETE or comment out this block:
location /media/ {
    alias /path/to/your/media/;
}
```

**Add** an internal-only location block that Nginx uses for X-Accel-Redirect:
```nginx
location /protected-media/ {
    internal;
    alias /path/to/your/media/;  # Replace with your actual MEDIA_ROOT path
}
```

This `internal` directive means the `/protected-media/` path is **completely inaccessible from the public internet** — only Django's `X-Accel-Redirect` header can trigger it. Direct browser requests to `/protected-media/anything` will return 404.

**Ensure** all other requests pass through Django as normal (your existing `location /` proxy_pass block handles this).

### Step 5 — Verify Nginx config and reload

After editing the config:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Verification

After implementing both parts:

1. While **logged out**, attempt to access a known media file URL directly (e.g. `https://ecofleetexpress.com/media/attendance/attendance_june2026.xlsx`). You should be redirected to the login page, not served the file.

2. While **logged in as staff**, access the same URL. The file should download normally.

3. Attempt to access `/protected-media/attendance/attendance_june2026.xlsx` directly in the browser. It should return 404 (Nginx `internal` block blocks it).

4. Run `python manage.py check` — should still pass with 0 issues.

---

## Notes

- In **local development** (`NGINX_ACCEL_REDIRECT=False`), Django streams the file directly via `FileResponse`. This is slightly less efficient but works without Nginx.
- In **production** (`NGINX_ACCEL_REDIRECT=True`), Django handles auth and then hands off to Nginx for actual file delivery via X-Accel-Redirect. This is the efficient production pattern.
- The path traversal check (`os.path.realpath` comparison) ensures a crafted URL like `/media/../../settings.py` cannot escape the media root.