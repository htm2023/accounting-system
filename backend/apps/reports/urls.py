from django.urls import path
from .views import TrialBalanceView, IncomeStatementView, BalanceSheetView, PartyStatementView, CashFlowView

urlpatterns = [
    path('trial-balance/', TrialBalanceView.as_view(), name='trial-balance'),
    path('income-statement/', IncomeStatementView.as_view(), name='income-statement'),
    path('balance-sheet/', BalanceSheetView.as_view(), name='balance-sheet'),
    path('party-statement/<int:party_id>/', PartyStatementView.as_view(), name='party-statement'),
    path('cash-flow/', CashFlowView.as_view(), name='cash-flow'),
]
