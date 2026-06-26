# Deployment Checklist

## Environment Variables
- [ ] `DJANGO_SECRET_KEY` is set to a secure, random string.
- [ ] `DEBUG` is set to `False`.
- [ ] `ENVIRONMENT` is set to `production`.
- [ ] `ADMIN_EMAIL` is set.
- [ ] Email host configurations (`EMAIL_HOST`, `EMAIL_PORT`, etc.) are accurate.

## Database
- [ ] Migrations applied: `python manage.py migrate`
- [ ] Administrator created: `python manage.py createsuperuser`
- [ ] Database backup tested.

## Static and Media
- [ ] Run `python manage.py collectstatic --noinput`
- [ ] Ensure `media/` folder exists and is writable by the web server.

## Security
- [ ] SSL configured correctly (reverse proxy like Nginx/Apache handling HTTPS).
- [ ] Review `django-csp` headers in Production.
- [ ] Sentry DSN loaded (optional, but recommended).

## Operations
- [ ] Setup cron job for automated backups: `0 2 * * * cd /path/to/app && venv/bin/python manage.py backup_database`
- [ ] Setup cron job for database optimization: `0 3 * * 0 cd /path/to/app && venv/bin/python manage.py optimize_database`
