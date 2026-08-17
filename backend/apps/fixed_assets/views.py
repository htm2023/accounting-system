from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FixedAsset, DepreciationSchedule
from .serializers import FixedAssetSerializer, DepreciationScheduleSerializer
from apps.common.permissions import IsAccountant, IsAdmin

class FixedAssetViewSet(viewsets.ModelViewSet):
    queryset = FixedAsset.objects.all()
    serializer_class = FixedAssetSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

class DepreciationScheduleViewSet(viewsets.ModelViewSet):
    queryset = DepreciationSchedule.objects.all()
    serializer_class = DepreciationScheduleSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        elif self.action == 'post':
            self.permission_classes = [IsAdmin]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_update(self, serializer):
        if serializer.instance.is_posted:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError('Posted depreciation cannot be modified.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.is_posted:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError('Posted depreciation cannot be deleted.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        schedule = self.get_object()
        try:
            journal_entry = schedule.post(user=request.user)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'message': 'Depreciation posted successfully.',
            'journal_entry': journal_entry.entry_number
        })
