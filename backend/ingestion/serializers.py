from rest_framework import serializers
from core.models import Tenant, IngestionRun, EmissionRow, EditLog


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'created_at']


class IngestionRunSerializer(serializers.ModelSerializer):
    source_type_display = serializers.CharField(
        source='get_source_type_display', read_only=True
    )

    class Meta:
        model = IngestionRun
        fields = [
            'id', 'source_type', 'source_type_display', 'status',
            'row_count', 'error_count', 'uploaded_at', 'completed_at', 'error_log'
        ]


class EmissionRowSerializer(serializers.ModelSerializer):
    scope_display = serializers.CharField(
        source='get_scope_display', read_only=True
    )
    review_status_display = serializers.CharField(
        source='get_review_status_display', read_only=True
    )
    source_type = serializers.CharField(
        source='ingestion_run.get_source_type_display', read_only=True
    )
    run_id = serializers.CharField(
        source='ingestion_run_id', read_only=True
    )

    class Meta:
        model = EmissionRow
        fields = [
            'id', 'scope', 'scope_display', 'scope_justification',
            'category', 'subcategory',
            'raw_quantity', 'raw_unit', 'raw_date_str',
            'quantity_kgco2e', 'activity_date', 'period_start', 'period_end',
            'ef_value', 'ef_source',
            'review_status', 'review_status_display', 'flagged_reason',
            'audit_locked', 'audit_locked_at',
            'source_row_ref', 'source_type', 'run_id',
            'created_at', 'updated_at',
        ]


class EditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditLog
        fields = [
            'id', 'field_name', 'old_value',
            'new_value', 'reason', 'edited_at'
        ]