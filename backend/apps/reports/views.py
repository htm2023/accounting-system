from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Q
from apps.journal_entries.models import JournalEntry, JournalEntryLine
from apps.chart_of_accounts.models import Account
from apps.parties.models import Party
from apps.fiscal.models import FiscalPeriod


def as_of_filters(fiscal_period_id):
    """
    فلتر تراكمي حتى نهاية فترة مالية معيّنة (وليس حركات تلك الفترة فقط) —
    مناسب لحسابات الميزانية العمومية وميزان المراجعة، التي تعكس رصيدًا
    متراكمًا منذ البداية وليس مقيّدًا بفترة واحدة.
    """
    filters = Q(journal_entry__is_posted=True)
    if fiscal_period_id:
        try:
            period = FiscalPeriod.objects.get(id=fiscal_period_id)
        except FiscalPeriod.DoesNotExist:
            return None, Response({'error': 'Fiscal period not found.'}, status=status.HTTP_404_NOT_FOUND)
        filters &= Q(journal_entry__date__lte=period.end_date)
    return filters, None


class TrialBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fiscal_period_id = request.query_params.get('fiscal_period')
        filters, error_response = as_of_filters(fiscal_period_id)
        if error_response:
            return error_response

        lines = JournalEntryLine.objects.filter(filters).values('account__code', 'account__name_ar', 'account__name_en', 'account__account_type').annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        ).order_by('account__code')

        data = []
        for line in lines:
            debit = line['total_debit'] or 0
            credit = line['total_credit'] or 0
            balance = debit - credit
            data.append({
                'account_code': line['account__code'],
                'account_name_ar': line['account__name_ar'],
                'account_name_en': line['account__name_en'],
                'account_type': line['account__account_type'],
                'total_debit': debit,
                'total_credit': credit,
                'balance': balance
            })
        return Response(data)

class IncomeStatementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fiscal_period_id = request.query_params.get('fiscal_period')
        filters = Q()
        if fiscal_period_id:
            filters &= Q(journal_entry__fiscal_period_id=fiscal_period_id)
        else:
            filters &= Q(journal_entry__is_posted=True)

        # الإيرادات
        revenue_lines = JournalEntryLine.objects.filter(
            filters,
            account__account_type=Account.AccountType.REVENUE
        ).aggregate(total=Sum('credit') - Sum('debit'))['total'] or 0

        # المصروفات
        expense_lines = JournalEntryLine.objects.filter(
            filters,
            account__account_type=Account.AccountType.EXPENSE
        ).aggregate(total=Sum('debit') - Sum('credit'))['total'] or 0

        net_profit = revenue_lines - expense_lines
        return Response({
            'revenue': revenue_lines,
            'expenses': expense_lines,
            'net_profit': net_profit
        })

class BalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fiscal_period_id = request.query_params.get('fiscal_period')
        filters, error_response = as_of_filters(fiscal_period_id)
        if error_response:
            return error_response

        # الأصول
        assets = JournalEntryLine.objects.filter(
            filters,
            account__account_type=Account.AccountType.ASSET
        ).aggregate(total=Sum('debit') - Sum('credit'))['total'] or 0

        # الالتزامات
        liabilities = JournalEntryLine.objects.filter(
            filters,
            account__account_type=Account.AccountType.LIABILITY
        ).aggregate(total=Sum('credit') - Sum('debit'))['total'] or 0

        # حقوق الملكية
        equity = JournalEntryLine.objects.filter(
            filters,
            account__account_type=Account.AccountType.EQUITY
        ).aggregate(total=Sum('credit') - Sum('debit'))['total'] or 0

        return Response({
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_liabilities_equity': liabilities + equity
        })

class PartyStatementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, party_id):
        try:
            party = Party.objects.get(id=party_id)
        except Party.DoesNotExist:
            return Response({'error': 'Party not found.'}, status=status.HTTP_404_NOT_FOUND)

        # جميع حركات الطرف من القيود المرحّلة
        entries = JournalEntryLine.objects.filter(
            journal_entry__is_posted=True,
            account=party.default_account
        ).select_related('journal_entry').order_by('journal_entry__date', 'journal_entry__created_at')

        data = []
        running_balance = 0
        for line in entries:
            debit = line.debit or 0
            credit = line.credit or 0
            running_balance += debit - credit
            data.append({
                'date': line.journal_entry.date,
                'description': line.description or line.journal_entry.description,
                'debit': debit,
                'credit': credit,
                'balance': running_balance
            })

        return Response({
            'party': party.name_ar,
            'opening_balance': party.opening_balance,
            'entries': data,
            'closing_balance': running_balance + party.opening_balance
        })

class CashFlowView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fiscal_period_id = request.query_params.get('fiscal_period')
        filters = Q(journal_entry__is_posted=True)
        if fiscal_period_id:
            filters &= Q(journal_entry__fiscal_period_id=fiscal_period_id)

        cash_accounts = Account.objects.filter(
            is_cash_account=True,
            account_type=Account.AccountType.ASSET
        )

        cash_lines = JournalEntryLine.objects.filter(
            filters,
            account__in=cash_accounts
        )

        inflow = cash_lines.filter(credit__gt=0).aggregate(total=Sum('credit'))['total'] or 0
        outflow = cash_lines.filter(debit__gt=0).aggregate(total=Sum('debit'))['total'] or 0

        return Response({
            'cash_inflow': inflow,
            'cash_outflow': outflow,
            'net_cash_flow': inflow - outflow
        })
