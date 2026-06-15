from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

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
        jude.set_password('Jude123')
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
        jude_profile.save()

        self.stdout.write(self.style.SUCCESS("Superuser 'Jude' (Director) updated/created successfully."))

        jitendra, created = User.objects.get_or_create(
            username='Jitendra',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Jitendra',
                'last_name': '',
            }
        )
        jitendra.set_password('Jitendra123')
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
        jitendra_profile.save()

        self.stdout.write(self.style.SUCCESS("Superuser 'Jitendra' (Manager) updated/created successfully."))
