import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'ecofleet.settings'

import django
from django.core.exceptions import ImproperlyConfigured
import sys

def test_config(env_val):
    os.environ['DJANGO_CSRF_TRUSTED_ORIGINS'] = env_val
    try:
        # Reload the settings module to re-evaluate it
        import importlib
        import ecofleet.settings
        importlib.reload(ecofleet.settings)
        print(f"SUCCESS for '{env_val}': {ecofleet.settings.CSRF_TRUSTED_ORIGINS}")
    except ImproperlyConfigured as e:
        print(f"FAILED (ImproperlyConfigured) for '{env_val}': {e}")
    except Exception as e:
        print(f"FAILED (Exception) for '{env_val}': {e}")

test_config('')
test_config(' ')
test_config('https://example.com')
test_config('https://example.com, https://staging.example.com ')
test_config('https://example.com,,https://staging.example.com')
test_config('http://example.com')
test_config('example.com') # Should fail
test_config('https://')
