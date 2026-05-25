import uuid
from django.db import models
from django.contrib.auth.models import User


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EmissionFactor(models.Model):
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=200)
    unit_from = models.CharField(max_length=50)
    factor = models.DecimalField(max_digits=12, decimal_places=6)
    source = models.CharField(max_length=200)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    region = models.CharField(max_length=10, default='GLOBAL')

    def __str__(self):
        return f"{self.subcategory} ({self.unit_from}) → kgCO2e"


class IngestionRun(models.Model):
    SOURCE_CHOICES = [
        ('SAP_FLAT_FILE', 'SAP Flat File'),
        ('UTILITY_CSV', 'Utility CSV'),
        ('TRAVEL_JSON', 'Travel JSON'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    raw_file = models.FileField(upload_to='runs/', null=True, blank=True)
    file_checksum = models.CharField(max_length=64, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_log = models.JSONField(default=list)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.source_type} run {self.id} ({self.status})"


class EmissionRow(models.Model):
    SCOPE_CHOICES = [
        ('SCOPE_1', 'Scope 1'),
        ('SCOPE_2', 'Scope 2'),
        ('SCOPE_3', 'Scope 3'),
    ]
    REVIEW_CHOICES = [
        ('PENDING', 'Pending'),
        ('FLAGGED', 'Flagged'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    ingestion_run = models.ForeignKey(
        IngestionRun, on_delete=models.CASCADE, related_name='rows'
    )
    source_row_ref = models.CharField(max_length=200, blank=True)

    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    scope_justification = models.TextField(blank=True)
    category = models.CharField(max_length=200)
    subcategory = models.CharField(max_length=200, blank=True)

    raw_quantity = models.DecimalField(max_digits=16, decimal_places=4, null=True)
    raw_unit = models.CharField(max_length=50, blank=True)
    raw_date_str = models.CharField(max_length=50, blank=True)

    quantity_kgco2e = models.DecimalField(max_digits=16, decimal_places=4, null=True)
    activity_date = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    emission_factor = models.ForeignKey(
        EmissionFactor, on_delete=models.SET_NULL, null=True, blank=True
    )
    ef_value = models.DecimalField(max_digits=12, decimal_places=6, null=True)
    ef_source = models.CharField(max_length=200, blank=True)

    review_status = models.CharField(
        max_length=20, choices=REVIEW_CHOICES, default='PENDING'
    )
    flagged_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_rows'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    audit_locked = models.BooleanField(default=False)
    audit_locked_at = models.DateTimeField(null=True, blank=True)
    audit_locked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='locked_rows'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category} | {self.scope} | {self.quantity_kgco2e} kgCO2e"


class EditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emission_row = models.ForeignKey(
        EmissionRow, on_delete=models.CASCADE, related_name='edits'
    )
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    edited_at = models.DateTimeField(auto_now_add=True)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField()
    new_value = models.TextField()
    reason = models.TextField()

    def __str__(self):
        return f"Edit to {self.emission_row_id} by {self.edited_by}"
