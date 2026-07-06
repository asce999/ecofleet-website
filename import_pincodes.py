import json
import os
import django
import sys

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecofleet.settings')
django.setup()

from core.models import Pincode

print("Reading datadump...")
with open('datadump_core_safe.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {len(data)} items from JSON.")
pincodes_to_create = []

for item in data:
    if item.get('model') == 'core.pincode':
        pincodes_to_create.append(Pincode(
            pin=item['fields']['pin'],
            city=item['fields']['city'],
            state=item['fields']['state'],
            location_type=item['fields']['location_type']
        ))

print(f"Found {len(pincodes_to_create)} pincodes. Starting bulk upload in batches of 1000...")

# Load them in chunks to save memory!
try:
    # Use ignore_conflicts so if it partially loaded before crashing, it won't crash on duplicate keys
    Pincode.objects.bulk_create(pincodes_to_create, batch_size=1000, ignore_conflicts=True)
    print("SUCCESS: All pincodes have been successfully uploaded to the database!")
except Exception as e:
    print(f"ERROR during bulk create: {e}")
