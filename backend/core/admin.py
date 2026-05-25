from django.contrib import admin
from core.models import Tenant, EmissionFactor, IngestionRun, EmissionRow, EditLog


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'slug']


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ['category', 'subcategory', 'unit_from', 'factor', 'source', 'region', 'valid_from']
    list_filter = ['category', 'region']
    search_fields = ['subcategory', 'source']


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'tenant', 'source_type', 'status', 'row_count', 'error_count', 'uploaded_at']
    list_filter = ['source_type', 'status', 'tenant']
    readonly_fields = ['id', 'file_checksum', 'uploaded_at', 'completed_at', 'error_log']


@admin.register(EmissionRow)
class EmissionRowAdmin(admin.ModelAdmin):
    list_display = ['id', 'tenant', 'scope', 'category', 'quantity_kgco2e', 'review_status', 'audit_locked']
    list_filter = ['scope', 'review_status', 'audit_locked', 'tenant']
    search_fields = ['category', 'subcategory', 'source_row_ref']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(EditLog)
class EditLogAdmin(admin.ModelAdmin):
    list_display = ['emission_row', 'edited_by', 'field_name', 'edited_at']
    readonly_fields = ['id', 'edited_at']
