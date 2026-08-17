from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Currency, ExchangeRateHistory
from .serializers import CurrencySerializer, ExchangeRateHistorySerializer
from apps.common.permissions import IsAccountant

class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

class ExchangeRateHistoryViewSet(viewsets.ModelViewSet):
    queryset = ExchangeRateHistory.objects.all()
    serializer_class = ExchangeRateHistorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
