from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentSequenceViewSet

router = DefaultRouter()
router.register(r'sequences', DocumentSequenceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
