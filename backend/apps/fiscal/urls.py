from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FiscalYearViewSet, FiscalPeriodViewSet

router = DefaultRouter()
router.register(r'years', FiscalYearViewSet)
router.register(r'periods', FiscalPeriodViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
