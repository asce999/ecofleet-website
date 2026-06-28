# EcoFleet Express Deployment Guide

## Overview
This document outlines the deployment configurations required to run EcoFleet Express securely in staging and production environments, specifically focusing on reverse proxy compatibility and CSRF protection.

## Required Environment Variables

When deploying behind a reverse proxy (e.g. Nginx, ALB, Cloudflare) that terminates TLS/HTTPS, specific environment variables must be configured to ensure Django's security middleware functions correctly.

### `DJANGO_CSRF_TRUSTED_ORIGINS`
Django (>=4.0) strictly validates the `Origin` and `Referer` headers for unsafe requests (POST, PUT, DELETE). When an HTTPS reverse proxy forwards requests to an HTTP Django backend, the scheme mismatch triggers a CSRF failure unless explicitly trusted.

* **Format**: Comma-separated list of origins.
* **Requirement**: The scheme (`http://` or `https://`) MUST be included.
* **Example**: `https://example.com,https://staging.example.com`

### `DJANGO_ALLOWED_HOSTS`
The domain names that the Django application is permitted to serve.
* **Format**: Comma-separated list of hostnames (no scheme).
* **Example**: `example.com,staging.example.com`

---

## Configuration Profiles

### 1. Local Development
For local testing (e.g., `python manage.py runserver`), the Django development server operates over standard HTTP. The `Origin` and `Host` headers intrinsically match.
* `DJANGO_ALLOWED_HOSTS`: Can be left unset (defaults to `127.0.0.1,localhost`).
* `DJANGO_CSRF_TRUSTED_ORIGINS`: Can be left unset (defaults to empty).

### 2. Staging Environment
Staging typically mirrors production but on a subdomain.
* `DJANGO_ALLOWED_HOSTS=staging.example.com`
* `DJANGO_CSRF_TRUSTED_ORIGINS=https://staging.example.com`

### 3. Production Environment
Production must handle both the root domain and `www` alias securely.
* `DJANGO_ALLOWED_HOSTS=example.com,www.example.com`
* `DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com`

---

## Interaction Between ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS

Both settings are critical, independent layers of security:

1. **`ALLOWED_HOSTS` (Host Header Validation)**
   - Protects against HTTP Host header attacks.
   - Checked on **every** request.
   - Defines *who the server thinks it is*.
   - Contains just the hostname (e.g. `example.com`).

2. **`CSRF_TRUSTED_ORIGINS` (Origin Validation)**
   - Protects against Cross-Site Request Forgery (CSRF).
   - Checked on **unsafe** requests (POST, PUT, etc.).
   - Defines *who is allowed to send state-changing requests to the server*.
   - Contains the exact scheme and hostname (e.g. `https://example.com`).

**Why both are required behind a proxy**: The proxy alters the edge request. `ALLOWED_HOSTS` verifies the target domain is correct, while `CSRF_TRUSTED_ORIGINS` explicitly tells Django that the TLS-terminated origin (`https://...`) is safe despite Django receiving an HTTP connection locally.
