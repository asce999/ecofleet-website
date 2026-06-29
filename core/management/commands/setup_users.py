from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
from django.utils.crypto import get_random_string
import os

class Command(BaseCommand):
    help = 'Create Jude (Director) and Jitendra (Manager) superuser accounts.'

    def handle(self, *args, **options):
        jude, created = User.objects.get_or_create(
            username='Jude',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Jude',
                'last_name': '',
            }
        )
        env_password = os.getenv('ECOFLEET_BOOTSTRAP_PASSWORD')
        jude_password = env_password or get_random_string(12)
        jude.set_password(jude_password)
        jude.is_staff = True
        jude.is_superuser = True
        jude.last_name = ''
        jude.save()

        jude_profile, _ = UserProfile.objects.get_or_create(user=jude)
        jude_profile.role = 'Director'
        jude_profile.can_use_cof = True
        jude_profile.can_use_morning = True
        jude_profile.can_use_pendency = True
        jude_profile.can_use_prev_month = True
        jude_profile.can_use_btpl = True
        jude_profile.can_use_attendance = True
        jude_profile.save()

        if not env_password:
            self.stdout.write(self.style.SUCCESS(f"Superuser 'Jude' (Director) updated/created successfully. Initial Password: {jude_password} - CHANGE IMMEDIATELY."))
        else:
            self.stdout.write(self.style.SUCCESS("Superuser 'Jude' (Director) updated/created successfully using provided bootstrap password."))

        jitendra, created = User.objects.get_or_create(
            username='Jitendra',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Jitendra',
                'last_name': '',
            }
        )
        jitendra_password = env_password or get_random_string(12)
        jitendra.set_password(jitendra_password)
        jitendra.is_staff = True
        jitendra.is_superuser = True
        jitendra.last_name = ''
        jitendra.save()

        jitendra_profile, _ = UserProfile.objects.get_or_create(user=jitendra)
        jitendra_profile.role = 'Manager'
        jitendra_profile.can_use_cof = True
        jitendra_profile.can_use_morning = True
        jitendra_profile.can_use_pendency = True
        jitendra_profile.can_use_prev_month = True
        jitendra_profile.can_use_btpl = True
        jitendra_profile.can_use_attendance = True
        jitendra_profile.save()

        if not env_password:
            self.stdout.write(self.style.SUCCESS(f"Superuser 'Jitendra' (Manager) updated/created successfully. Initial Password: {jitendra_password} - CHANGE IMMEDIATELY."))
        else:
            self.stdout.write(self.style.SUCCESS("Superuser 'Jitendra' (Manager) updated/created successfully using provided bootstrap password."))
