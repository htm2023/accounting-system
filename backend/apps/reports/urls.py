from django.urls import path
from .views import TrialBalanceView, IncomeStatementView, BalanceSheetView, PartyStatementView, CashFlowView
from .export_views import (
    TrialBalanceExportView,
    IncomeStatementExportView,
    BalanceSheetExportView,
    CashFlowExportView,
    PartyStatementExportView,
)
from .pdf_export_views import (
    TrialBalancePDFView,
    IncomeStatementPDFView,
    BalanceSheetPDFView,
    CashFlowPDFView,
    PartyStatementPDFView,
)

urlpatterns = [
    path('trial-balance/', TrialBalanceView.as_view(), name='trial-balance'),
    path('income-statement/', IncomeStatementView.as_view(), name='income-statement'),
    path('balance-sheet/', BalanceSheetView.as_view(), name='balance-sheet'),
    path('party-statement/<int:party_id>/', PartyStatementView.as_view(), name='party-statement'),
    path('cash-flow/', CashFlowView.as_view(), name='cash-flow'),
    path('trial-balance/export/', TrialBalanceExportView.as_view(), name='trial-balance-export'),
    path('income-statement/export/', IncomeStatementExportView.as_view(), name='income-statement-export'),
    path('balance-sheet/export/', BalanceSheetExportView.as_view(), name='balance-sheet-export'),
    path('cash-flow/export/', CashFlowExportView.as_view(), name='cash-flow-export'),
    path('party-statement/<int:party_id>/export/', PartyStatementExportView.as_view(), name='party-statement-export'),
    path('trial-balance/export-pdf/', TrialBalancePDFView.as_view(), name='trial-balance-pdf'),
    path('income-statement/export-pdf/', IncomeStatementPDFView.as_view(), name='income-statement-pdf'),
    path('balance-sheet/export-pdf/', BalanceSheetPDFView.as_view(), name='balance-sheet-pdf'),
    path('cash-flow/export-pdf/', CashFlowPDFView.as_view(), name='cash-flow-pdf'),
    path('party-statement/<int:party_id>/export-pdf/', PartyStatementPDFView.as_view(), name='party-statement-pdf'),
]
