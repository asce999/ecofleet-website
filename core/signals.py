from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from core.models import UserProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance)
