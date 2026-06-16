import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecofleet.settings')
django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS = ['testserver', '*']

from django.test import Client
from django.contrib.auth.models import User
from core.models import UserProfile

# Create a dummy superuser/staff for testing
user, created = User.objects.get_or_create(username='smoketest', is_staff=True, is_superuser=True)
if created:
    user.set_password('testpass')
    user.save()

profile, _ = UserProfile.objects.get_or_create(user=user)
profile.can_use_cof = True
profile.can_use_btpl = True
profile.can_use_ftl = True
profile.can_use_attendance = True
profile.save()

client = Client()
client.force_login(user)

routes = [
    '/portal/',
    '/portal/cof/',
    '/portal/btpl/',
    '/portal/ftl/',
    '/portal/attendance/',
    '/portal/morning-report/',
    '/portal/pendency/',
    '/portal/prev-month/',
]

errors = False
for r in routes:
    try:
        res = client.get(r)
        if res.status_code == 500:
            print(f"FAILED {r}: 500 Internal Server Error")
            errors = True
        else:
            print(f"SUCCESS {r}: {res.status_code}")
    except Exception as e:
        print(f"FAILED {r}: EXCEPTION {e}")
        errors = True

user.delete()
if errors:
    sys.exit(1)
