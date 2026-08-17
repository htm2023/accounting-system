from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CurrencyViewSet, ExchangeRateHistoryViewSet

router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet)
router.register(r'exchange-rates', ExchangeRateHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
