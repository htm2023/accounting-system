from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReceiptPaymentViewSet, PaymentAllocationViewSet

router = DefaultRouter()
router.register(r'receipts-payments', ReceiptPaymentViewSet, basename='receipt-payment')
router.register(r'allocations', PaymentAllocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
