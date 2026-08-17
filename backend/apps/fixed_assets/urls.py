from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FixedAssetViewSet, DepreciationScheduleViewSet

router = DefaultRouter()
router.register(r'assets', FixedAssetViewSet)
router.register(r'depreciation-schedules', DepreciationScheduleViewSet, basename='depreciation-schedule')

urlpatterns = [
    path('', include(router.urls)),
]
