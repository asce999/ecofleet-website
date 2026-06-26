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
    TOOL_ATTENDANCE = 'ATTENDANCE'
    TOOL_FTL = 'FTL'
    TOOL_CHOICES = [
        (TOOL_COF, 'COF Generator'),
        (TOOL_MORNING, 'Morning Report'),
        (TOOL_PENDENCY, 'Pendency Report'),
        (TOOL_PREV_MONTH, 'Previous Month Update'),
        (TOOL_BTPL, 'BTPL Sheet'),
        (TOOL_ATTENDANCE, 'Attendance Tracker'),
        (TOOL_FTL, 'FTL Tracker'),
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


class AttendanceWorkbook(models.Model):
    """The team's active Attendance workbook."""
    file = models.FileField(upload_to='attendance/')
    original_name = models.CharField(max_length=255)
    active_sheet = models.CharField(max_length=100, default='JUNE 2026')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='attendance_workbooks')
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_name} ({self.active_sheet}) ({'active' if self.is_active else 'archived'})"

    @classmethod
    def active(cls):
        return cls.objects.filter(is_active=True).first()


class SalaryConfig(models.Model):
    """Singleton model to store global payroll rates and settings."""
    basic_rate_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=492.12)
    sp_allowance_rate_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=96.58)
    standard_month_days = models.IntegerField(default=26)
    other_allowance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Percentage (e.g. 10.00)")
    other_allowance_eligible_departments = models.CharField(max_length=255, default="CV-SUPERVISOR,CV-DEO", help_text="Comma-separated list of departments")
    hra_pct = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, help_text="Percentage (e.g. 5.00)")
    
    leave_payment_threshold_days = models.DecimalField(max_digits=5, decimal_places=2, default=19.90)
    leave_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=589.00)
    extra_day_rate = models.DecimalField(max_digits=10, decimal_places=2, default=589.00)
    
    pf_wage_ceiling = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00)
    pf_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.00, help_text="Percentage (e.g. 12.00)")
    esic_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.75, help_text="Percentage (e.g. 0.75)")
    
    pt_slab_1_max = models.DecimalField(max_digits=10, decimal_places=2, default=7499.00)
    pt_slab_2_max = models.DecimalField(max_digits=10, decimal_places=2, default=9999.00)
    pt_slab_3_amount = models.DecimalField(max_digits=10, decimal_places=2, default=300.00, help_text="Usually 200, but 300 in Feb")
    
    canteen_rate_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=14.00)
    
    reporting_pf_cost_rate = models.DecimalField(max_digits=5, decimal_places=2, default=25.00, help_text="Percentage (e.g. 25.00)")
    reporting_esic_cost_rate = models.DecimalField(max_digits=5, decimal_places=2, default=4.00, help_text="Percentage (e.g. 4.00)")

    def __str__(self):
        return "Salary Configuration"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class EmployeeSalaryOverride(models.Model):
    """Stores manual overrides for an employee for the Salary Calculator."""
    employee_name = models.CharField(max_length=255, unique=True)
    adhoc_salary_increase_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Percentage (e.g. 25.00 for 25%)")
    adhoc_allowance_monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    advance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    lwf = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cash_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_name']

    def __str__(self):
        return f"{self.employee_name} Overrides"


class FtlWorkbook(models.Model):
    """The team's active FTL shipment workbook."""
    file = models.FileField(upload_to='ftl/')
    original_name = models.CharField(max_length=255)
    active_sheet = models.CharField(max_length=100, default='Sheet1')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ftl_workbooks')
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
    can_use_attendance = models.BooleanField(default=True)
    can_use_ftl = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} Profile ({self.role})"





class SystemEvent(models.Model):
    """Event log for all meaningful operational and business activities."""
    SEVERITY_INFO = 'INFO'
    SEVERITY_WARNING = 'WARNING'
    SEVERITY_CRITICAL = 'CRITICAL'
    SEVERITY_CHOICES = [
        (SEVERITY_INFO, 'Info'),
        (SEVERITY_WARNING, 'Warning'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_INFO)
    component = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    request_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    tool = models.CharField(max_length=50, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.severity}] {self.component} - {self.title} at {self.timestamp}"