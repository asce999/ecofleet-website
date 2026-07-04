from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
import uuid
from django.utils import timezone


class Pincode(models.Model):
    pin = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    location_type = models.CharField(max_length=10)  # ODA or Non-ODA

    def __str__(self):
        return f"{self.pin} - {self.city} ({self.location_type})"


class ToolRunQuerySet(models.QuerySet):
    def for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        try:
            if user.profile.role == UserProfile.ROLE_DIRECTOR:
                return self
        except ObjectDoesNotExist:
            pass
        return self.filter(user=user)


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

    objects = ToolRunQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tool', '-created_at']),
        ]

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
        """e.g. 'Morning Report Output (42)'"""
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
        indexes = [
            models.Index(fields=['is_active']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['is_active'],
                condition=Q(is_active=True),
                name='unique_active_cof'
            )
        ]

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
        indexes = [
            models.Index(fields=['is_active']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['is_active'],
                condition=Q(is_active=True),
                name='unique_active_btpl'
            )
        ]

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
        indexes = [
            models.Index(fields=['is_active']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['is_active'],
                condition=Q(is_active=True),
                name='unique_active_attendance'
            )
        ]

    def __str__(self):
        return f"{self.original_name} ({self.active_sheet}) ({'active' if self.is_active else 'archived'})"

    @classmethod
    def active(cls):
        return cls.objects.filter(is_active=True).first()


class SalaryConfig(models.Model):
    """Singleton model to store global payroll rates and settings."""
    basic_rate_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('492.12'))
    sp_allowance_rate_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('96.58'))
    standard_month_days = models.IntegerField(default=26)
    other_allowance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'), help_text="Percentage (e.g. 10.00)")
    other_allowance_eligible_departments = models.CharField(max_length=255, default="CV-SUPERVISOR,CV-DEO", help_text="Comma-separated list of departments")
    hra_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'), help_text="Percentage (e.g. 5.00)")
    
    leave_payment_threshold_days = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.90'))
    leave_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('589.00'))
    extra_day_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('589.00'))
    
    pf_wage_ceiling = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('15000.00'))
    pf_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('12.00'), help_text="Percentage (e.g. 12.00)")
    esic_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.75'), help_text="Percentage (e.g. 0.75)")
    
    pt_slab_1_max = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('7499.00'))
    pt_slab_2_max = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('9999.00'))
    pt_slab_3_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('300.00'), help_text="Usually 200, but 300 in Feb")
    
    canteen_rate_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('14.00'))
    
    reporting_pf_cost_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('25.00'), help_text="Percentage (e.g. 25.00)")
    reporting_esic_cost_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('4.00'), help_text="Percentage (e.g. 4.00)")

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
        indexes = [
            models.Index(fields=['is_active']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['is_active'],
                condition=Q(is_active=True),
                name='unique_active_ftl'
            )
        ]

    def __str__(self):
        return f"{self.original_name} ({self.active_sheet}) ({'active' if self.is_active else 'archived'})"

    @classmethod
    def active(cls):
        return cls.objects.filter(is_active=True).first()



class UserProfile(models.Model):
    ROLE_DIRECTOR = 'Director'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, default='Employee')
    can_use_cof = models.BooleanField(default=False)
    can_use_morning = models.BooleanField(default=False)
    can_use_pendency = models.BooleanField(default=False)
    can_use_prev_month = models.BooleanField(default=False)
    can_use_btpl = models.BooleanField(default=False)
    can_use_attendance = models.BooleanField(default=False)
    can_use_ftl = models.BooleanField(default=False)

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


# ==============================================================================
# PHASE 3: OPERATIONAL DATA MIGRATION (SHIPMENT DOMAIN)
# ==============================================================================

class MigrationFeatureFlags(models.Model):
    """Singleton model to control the rollout of Phase 3 database migration."""
    use_database_importer = models.BooleanField(
        default=False, 
        help_text="Shadow Mode: Uploaded Excel files are parsed and inserted into PostgreSQL."
    )
    use_database_reads = models.BooleanField(
        default=False, 
        help_text="Dual-Read: UI dashboards query PostgreSQL instead of parsing Excel."
    )  # TODO(phase-3): wired when dual-read/export lands
    use_database_exports = models.BooleanField(
        default=False, 
        help_text="Replaces static Excel downloads with dynamically generated DB workbooks."
    )

    def __str__(self):
        return "Migration Feature Flags"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


# ------------------------------------------------------------------------------
# FLEET CONTEXT (Master Data)
# ------------------------------------------------------------------------------

class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=100, blank=True)
    capacity_tons = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default='ACTIVE')

    def __str__(self):
        return self.registration_number


class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=100, blank=True)
    uan_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='ACTIVE')

    def __str__(self):
        return self.name

class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    is_driver = models.BooleanField(default=False)
    driver = models.OneToOneField(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


# ------------------------------------------------------------------------------
# CUSTOMER CONTEXT
# ------------------------------------------------------------------------------

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    gst_number = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ------------------------------------------------------------------------------
# SHIPMENT CONTEXT
# ------------------------------------------------------------------------------

class Shipment(models.Model):
    SHIPMENT_TYPE_CHOICES = [
        ('FTL', 'Full Truck Load'),
        ('BTPL', 'BTL Parcel Load'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment_type = models.CharField(max_length=10, choices=SHIPMENT_TYPE_CHOICES)
    origin = models.CharField(max_length=255, blank=True)
    destination = models.CharField(max_length=255, blank=True)
    
    # Using Lorry Number/Date as natural keys often found in Excel
    source_key = models.CharField(max_length=200, blank=True, db_index=True)
    dispatch_date = models.DateField(null=True, blank=True)
    expected_eta = models.DateTimeField(null=True, blank=True)
    actual_eta = models.DateTimeField(null=True, blank=True)
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')
    
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-dispatch_date']
        constraints = [
            UniqueConstraint(
                fields=['shipment_type', 'source_key'],
                condition=~Q(source_key=''),
                name='unique_shipment_source_key'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.source_key:
            lr = self.metadata.get('lr_number', '') if isinstance(self.metadata, dict) else ''
            date_str = self.dispatch_date.isoformat() if self.dispatch_date else ''
            self.source_key = f"{lr}|{date_str}"
            if self.source_key == "|":
                self.source_key = str(self.id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shipment_type} Shipment - {self.vehicle} on {self.dispatch_date}"


class ShipmentStatus(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('DISPATCHED', 'Dispatched'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='statuses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment} -> {self.status}"


class Consignment(models.Model):
    """Child entity of Shipment, especially relevant for BTPL"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='consignments')
    description = models.CharField(max_length=255, blank=True)
    weight = models.FloatField(null=True, blank=True)
    receiver = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_consignments')
    
    def __str__(self):
        return f"Consignment for {self.receiver} on {self.shipment}"


class TrackingHistory(models.Model):
    """Append-only ledger recording locations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_history')
    location = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']


# ------------------------------------------------------------------------------
# HUMAN RESOURCES CONTEXT
# ------------------------------------------------------------------------------

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'Leave'),
        ('HALF_DAY', 'Half Day'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='attendance_records')
    record_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    class Meta:
        unique_together = ('driver', 'record_date')
        ordering = ['-record_date']

    def __str__(self):
        return f"{self.driver} - {self.record_date} ({self.status})"


# ------------------------------------------------------------------------------
# IMPORT CONTEXT
# ------------------------------------------------------------------------------

class ImportJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PARTIAL_SUCCESS', 'Partial Success'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workbook_type = models.CharField(max_length=50) # 'FTL', 'BTPL', 'ATTENDANCE'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Import {self.workbook_type} - {self.status}"


class ImportErrorRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='errors')
    row_number = models.IntegerField()
    error_message = models.TextField()
    raw_data = models.JSONField(default=dict)

    class Meta:
        ordering = ['row_number']

    def __str__(self):
        return f"Error on {self.import_job} (Row {self.row_number})"
