import hashlib

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from core.models import Tenant, IngestionRun, EmissionRow, EditLog
from ingestion.serializers import (
    TenantSerializer, IngestionRunSerializer,
    EmissionRowSerializer, EditLogSerializer,
)
from ingestion.parsers import (
    parse_sap_flat_file,
    parse_utility_csv,
    parse_travel_json,
)


# ── TENANT ────────────────────────────────────────────────────────────────────

class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tenant.objects.all().order_by('name')
    serializer_class = TenantSerializer


# ── INGESTION RUN ─────────────────────────────────────────────────────────────

class IngestionRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngestionRunSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-uploaded_at']

    def get_queryset(self):
        qs = IngestionRun.objects.all()
        tenant_id = self.request.query_params.get('tenant')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs

    @action(detail=True, methods=['get'], url_path='rows')
    def rows(self, request, pk=None):
        run = self.get_object()
        rows = run.rows.all()
        review = request.query_params.get('review_status')
        if review:
            rows = rows.filter(review_status=review)
        serializer = EmissionRowSerializer(rows, many=True)
        return Response(serializer.data)


# ── EMISSION ROW ──────────────────────────────────────────────────────────────

class EmissionRowViewSet(viewsets.ModelViewSet):
    serializer_class = EmissionRowSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = EmissionRow.objects.select_related(
            'ingestion_run', 'reviewed_by', 'emission_factor'
        )
        params = self.request.query_params

        if tenant := params.get('tenant'):
            qs = qs.filter(tenant_id=tenant)
        if run := params.get('run'):
            qs = qs.filter(ingestion_run_id=run)
        if scope := params.get('scope'):
            qs = qs.filter(scope=scope)
        if review := params.get('review_status'):
            qs = qs.filter(review_status=review)
        if source := params.get('source_type'):
            qs = qs.filter(ingestion_run__source_type=source)

        return qs

    def _set_review_status(self, request, new_status):
        row = self.get_object()

        if row.audit_locked:
            return Response(
                {'detail': 'Row is audit-locked and cannot be changed.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        row.review_status = new_status
        row.reviewed_by = request.user if request.user.is_authenticated else None
        row.reviewed_at = timezone.now()

        if new_status == 'FLAGGED':
            row.flagged_reason = request.data.get('reason', row.flagged_reason)

        row.save(update_fields=[
            'review_status', 'reviewed_by', 'reviewed_at', 'flagged_reason'
        ])
        return Response(EmissionRowSerializer(row).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return self._set_review_status(request, 'APPROVED')

    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        return self._set_review_status(request, 'FLAGGED')

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self._set_review_status(request, 'REJECTED')

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        row = self.get_object()
        if row.review_status != 'APPROVED':
            return Response(
                {'detail': 'Only approved rows can be audit-locked.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        row.audit_locked = True
        row.audit_locked_at = timezone.now()
        row.audit_locked_by = request.user if request.user.is_authenticated else None
        row.save(update_fields=['audit_locked', 'audit_locked_at', 'audit_locked_by'])
        return Response(EmissionRowSerializer(row).data)

    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        row = self.get_object()

        if row.audit_locked:
            return Response(
                {'detail': 'Row is audit-locked and cannot be edited.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        allowed_fields = {
            'scope', 'category', 'subcategory',
            'raw_quantity', 'raw_unit', 'quantity_kgco2e',
            'activity_date', 'period_start', 'period_end',
            'flagged_reason', 'review_status',
        }
        field = request.data.get('field')
        new_value = request.data.get('value')
        reason = request.data.get('reason', '')

        if not field or field not in allowed_fields:
            return Response(
                {'detail': f'Field {field!r} not editable.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_value = str(getattr(row, field, ''))

        EditLog.objects.create(
            emission_row=row,
            edited_by=request.user if request.user.is_authenticated else None,
            field_name=field,
            old_value=old_value,
            new_value=str(new_value),
            reason=reason,
        )

        setattr(row, field, new_value)
        row.save(update_fields=[field, 'updated_at'])

        return Response(EmissionRowSerializer(row).data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        row = self.get_object()
        edits = row.edits.order_by('-edited_at')
        return Response(EditLogSerializer(edits, many=True).data)


# ── UPLOAD ────────────────────────────────────────────────────────────────────

PARSER_MAP = {
    'SAP_FLAT_FILE': parse_sap_flat_file,
    'UTILITY_CSV':   parse_utility_csv,
    'TRAVEL_JSON':   parse_travel_json,
}


class UploadView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @transaction.atomic
    def post(self, request):
        source_type = request.data.get('source_type', '').upper()
        tenant_id   = request.data.get('tenant_id')
        uploaded    = request.FILES.get('file')

        if source_type not in PARSER_MAP:
            return Response(
                {'detail': f'source_type must be one of: {list(PARSER_MAP.keys())}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not tenant_id:
            return Response(
                {'detail': 'tenant_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(pk=tenant_id)
        except Tenant.DoesNotExist:
            return Response(
                {'detail': 'Tenant not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not uploaded:
            return Response(
                {'detail': 'No file uploaded.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_bytes = uploaded.read()
        checksum  = hashlib.sha256(raw_bytes).hexdigest()

        try:
            file_content = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            file_content = raw_bytes.decode('latin-1')

        run = IngestionRun.objects.create(
            tenant=tenant,
            source_type=source_type,
            file_checksum=checksum,
            uploaded_by=request.user if request.user.is_authenticated else None,
            status='PROCESSING',
        )

        uploaded.seek(0)
        run.raw_file.save(uploaded.name, uploaded, save=True)

        try:
            parser = PARSER_MAP[source_type]
            parsed_rows, errors = parser(file_content)

            emission_rows = [
                EmissionRow(tenant=tenant, ingestion_run=run, **r)
                for r in parsed_rows
            ]

            EmissionRow.objects.bulk_create(emission_rows, batch_size=500)

            run.status       = 'DONE'
            run.row_count    = len(emission_rows)
            run.error_count  = len(errors)
            run.error_log    = errors
            run.completed_at = timezone.now()
            run.save()

        except Exception as exc:
            run.status    = 'FAILED'
            run.error_log = [{'row': 0, 'field': 'fatal', 'message': str(exc)}]
            run.save()
            return Response(
                {'detail': f'Parsing failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            IngestionRunSerializer(run).data,
            status=status.HTTP_201_CREATED,
        )


# ── DASHBOARD STATS ───────────────────────────────────────────────────────────

class DashboardStatsView(APIView):

    def get(self, request):
        tenant_id = request.query_params.get('tenant')
        qs        = EmissionRow.objects.all()
        run_qs    = IngestionRun.objects.all()

        if tenant_id:
            qs     = qs.filter(tenant_id=tenant_id)
            run_qs = run_qs.filter(tenant_id=tenant_id)

        review_counts = {
            r['review_status']: r['count']
            for r in qs.values('review_status').annotate(count=Count('id'))
        }

        scope_counts = {
            r['scope']: r['count']
            for r in qs.values('scope').annotate(count=Count('id'))
        }

        scope_emissions = {
            r['scope']: float(r['total'] or 0)
            for r in qs.values('scope').annotate(total=Sum('quantity_kgco2e'))
        }

        source_counts = {
            r['ingestion_run__source_type']: r['count']
            for r in qs.values('ingestion_run__source_type').annotate(count=Count('id'))
        }

        recent_runs   = run_qs.order_by('-uploaded_at')[:5]
        total_kgco2e  = float(qs.aggregate(t=Sum('quantity_kgco2e'))['t'] or 0)

        return Response({
            'total_rows':       qs.count(),
            'total_kgco2e':     total_kgco2e,
            'review_breakdown': review_counts,
            'scope_breakdown':  scope_counts,
            'scope_emissions':  scope_emissions,
            'source_breakdown': source_counts,
            'recent_runs':      IngestionRunSerializer(recent_runs, many=True).data,
        })
