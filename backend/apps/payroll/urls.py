from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, PayslipViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'payslips', PayslipViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
