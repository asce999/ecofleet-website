import csv
from django.core.management.base import BaseCommand
from core.models import Pincode

class Command(BaseCommand):
    help = 'Import pincodes from CSV'

    def handle(self, *args, **kwargs):
        with open('Pin-Code_List_9Jun26.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                Pincode.objects.get_or_create(
                    pin=row['Pin'].strip(),
                    defaults={
                        'city': row['City'].strip(),
                        'state': row['State'].strip(),
                        'location_type': row['ODA / Non-ODA Location'].strip(),
                    }
                )
                count += 1
            self.stdout.write(f'Successfully imported {count} pincodes')