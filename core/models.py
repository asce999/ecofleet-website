from django.conf import settings
from django.db import models


class Pincode(models.Model):
    pin = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    location_type = models.CharField(max_length=10)  # ODA or Non-ODA

    def __str__(self):
        return f"{self.pin} - {self.city} ({self.location_type})"


class ToolRun(models.Model):
    """Audit log of every automation run — powers the dashboard stats & activity feed."""

    TOOL_COF = 'COF'
    TOOL_MORNING = 'MORNING'
    TOOL_PENDENCY = 'PENDENCY'
    TOOL_PREV_MONTH = 'PREV_MONTH'
    TOOL_BTPL = 'BTPL'
    TOOL_CHOICES = [
        (TOOL_COF, 'COF Generator'),
        (TOOL_MORNING, 'Morning Report'),
        (TOOL_PENDENCY, 'Pendency Report'),
        (TOOL_PREV_MONTH, 'Previous Month Update'),
        (TOOL_BTPL, 'BTPL Sheet'),
    ]

    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tool_runs',
    )
    tool = models.CharField(max_length=20, choices=TOOL_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    reference = models.CharField(max_length=120, blank=True)   # e.g. COF number
    detail = models.TextField(blank=True)
    output_file = models.FileField(upload_to='tool_outputs/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tool_display()} · {self.created_at:%d-%b-%Y %H:%M} · {self.status}"


class ToolRunFile(models.Model):
    """An output file produced by a ToolRun (a run can produce several)."""
    run = models.ForeignKey(ToolRun, on_delete=models.CASCADE, related_name='files')
    label = models.CharField(max_length=80)
    file = models.FileField(upload_to='tool_outputs/%Y/%m/')
    download_name = models.CharField(max_length=255, blank=True)  # user-facing filename
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.label} ({self.run_id})"


class CofWorkbook(models.Model):
    """The team's active COF tracking workbook (one current row at a time)."""
    file = models.FileField(upload_to='cof/')
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cof_workbooks')
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_name} ({'active' if self.is_active else 'archived'})"

    @classmethod
    def active(cls):
        return cls.objects.filter(is_active=True).first()


class BtplWorkbook(models.Model):
    """The team's active BTPL shipment workbook."""
    file = models.FileField(upload_to='btpl/')
    original_name = models.CharField(max_length=255)
    active_sheet = models.CharField(max_length=100, default='JUN 26')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='btpl_workbooks')
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_name} ({self.active_sheet}) ({'active' if self.is_active else 'archived'})"

    @classmethod
    def active(cls):
        return cls.objects.filter(is_active=True).first()



class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, default='Employee')
    can_use_cof = models.BooleanField(default=True)
    can_use_morning = models.BooleanField(default=True)
    can_use_pendency = models.BooleanField(default=True)
    can_use_prev_month = models.BooleanField(default=True)
    can_use_btpl = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} Profile ({self.role})"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance)