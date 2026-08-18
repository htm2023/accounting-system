from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JournalEntryViewSet, CloseFiscalPeriodView

router = DefaultRouter()
router.register(r'entries', JournalEntryViewSet, basename='journal-entry')

urlpatterns = [
    path('', include(router.urls)),
    path('close-period/<int:period_id>/', CloseFiscalPeriodView.as_view(), name='close-fiscal-period'),
]
