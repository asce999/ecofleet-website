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
    TOOL_CHOICES = [
        (TOOL_COF, 'COF Generator'),
        (TOOL_MORNING, 'Morning Report'),
        (TOOL_PENDENCY, 'Pendency Report'),
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
