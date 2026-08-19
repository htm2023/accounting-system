from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import JournalEntry
from .serializers import JournalEntrySerializer
from apps.common.permissions import IsAccountant, IsAdmin
from .services import close_fiscal_period
from apps.fiscal.models import FiscalPeriod
from apps.audit_logs.services import log_action
from apps.audit_logs.models import AuditLog

class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.prefetch_related('lines')
    serializer_class = JournalEntrySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        elif self.action == 'post':
            self.permission_classes = [IsAdmin]
        elif self.action == 'reverse':
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        if instance.is_posted:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Posted journal entries cannot be deleted.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        entry = self.get_object()
        try:
            entry.post(user=request.user)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        log_action(
            user=request.user,
            action=AuditLog.Action.POST,
            model_name='JournalEntry',
            object_id=entry.id,
            description=f'Post journal entry {entry.entry_number}',
            request=request
        )
        return Response({'message': 'Entry posted successfully.', 'entry_number': entry.entry_number})

    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        entry = self.get_object()
        try:
            reversal = entry.create_reversal(user=request.user, date=request.data.get('date'))
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        log_action(
            user=request.user,
            action=AuditLog.Action.REVERSE,
            model_name='JournalEntry',
            object_id=entry.id,
            description=f'Reverse journal entry {entry.entry_number}',
            request=request
        )
        return Response(JournalEntrySerializer(reversal).data, status=status.HTTP_201_CREATED)

class CloseFiscalPeriodView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, period_id):
        try:
            entry = close_fiscal_period(period_id, user=request.user)
        except FiscalPeriod.DoesNotExist:
            return Response({'error': 'Fiscal period not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        log_action(
            user=request.user,
            action=AuditLog.Action.CLOSE,
            model_name='FiscalPeriod',
            object_id=period_id,
            description=f'Close fiscal period {period_id}',
            request=request
        )
        return Response({
            'message': f'تم إقفال الفترة بنجاح',
            'journal_entry': entry.entry_number
        }, status=status.HTTP_200_OK)
