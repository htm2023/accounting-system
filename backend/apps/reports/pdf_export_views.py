from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

from apps.parties.models import Party
from apps.fiscal.models import FiscalPeriod
from .export_views import (
    get_trial_balance_data,
    get_income_statement_data,
    get_balance_sheet_data,
    get_cash_flow_data,
    get_party_statement_data,
)

# خط Helvetica القياسي في reportlab لا يحتوي أي رموز عربية (ترميز WinAnsi)،
# فكانت النصوص العربية تُطبع كمربعات فارغة. Arial Unicode MS يغطي العربية.
ARABIC_FONT_NAME = 'ArialUnicode'
_ARABIC_FONT_PATH = r'C:\Windows\Fonts\ARIALUNI.TTF'
if ARABIC_FONT_NAME not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont(ARABIC_FONT_NAME, _ARABIC_FONT_PATH))


def format_text(value):
    """
    يشكّل الحروف العربية المتصلة ويرتبها من اليمين لليسار لعرضها بشكل صحيح
    في PDF (reportlab لا يقوم بذلك تلقائيًا). آمن أيضًا مع النصوص الإنجليزية
    والأرقام لأن reshape/get_display لا يغيّران النصوص غير العربية.
    """
    text = str(value)
    return get_display(arabic_reshaper.reshape(text))


def build_pdf_response(title, headers, rows, filename):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=1,
        fontName=ARABIC_FONT_NAME,
        fontSize=16,
        spaceAfter=12,
    )
    elements.append(Paragraph(format_text(title), title_style))
    elements.append(Spacer(1, 0.2 * inch))

    table_data = [[format_text(cell) for cell in headers]]
    table_data += [[format_text(cell) for cell in row] for row in rows]
    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), ARABIC_FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), ARABIC_FONT_NAME),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    doc.build(elements)
    return response


class TrialBalancePDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fiscal_period_id = request.query_params.get('fiscal_period')
        try:
            data = get_trial_balance_data(fiscal_period_id)
        except FiscalPeriod.DoesNotExist:
            return Response({'error': 'Fiscal period not found.'}, status=status.HTTP_404_NOT_FOUND)
        headers = ['Account Code', 'Account Name', 'Type', 'Debit', 'Credit', 'Balance']
        rows = [[d['account_code'], d['account_name_ar'], d['account_type'], d['total_debit'], d['total_credit'], d['balance']] for d in data]
        return build_pdf_response('Trial Balance', headers, rows, 'trial_balance.pdf')


class IncomeStatementPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fiscal_period_id = request.query_params.get('fiscal_period')
        data = get_income_statement_data(fiscal_period_id)
        headers = ['Item', 'Amount']
        rows = [
            ['Revenue', data['revenue']],
            ['Expenses', data['expenses']],
            ['Net Profit', data['net_profit']],
        ]
        return build_pdf_response('Income Statement', headers, rows, 'income_statement.pdf')


class BalanceSheetPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fiscal_period_id = request.query_params.get('fiscal_period')
        try:
            data = get_balance_sheet_data(fiscal_period_id)
        except FiscalPeriod.DoesNotExist:
            return Response({'error': 'Fiscal period not found.'}, status=status.HTTP_404_NOT_FOUND)
        headers = ['Item', 'Amount']
        rows = [
            ['Assets', data['assets']],
            ['Liabilities', data['liabilities']],
            ['Equity', data['equity']],
            ['Total Liabilities & Equity', data['total_liabilities_equity']],
        ]
        return build_pdf_response('Balance Sheet', headers, rows, 'balance_sheet.pdf')


class CashFlowPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fiscal_period_id = request.query_params.get('fiscal_period')
        data = get_cash_flow_data(fiscal_period_id)
        headers = ['Item', 'Amount']
        rows = [
            ['Cash Inflow', data['cash_inflow']],
            ['Cash Outflow', data['cash_outflow']],
            ['Net Cash Flow', data['net_cash_flow']],
        ]
        return build_pdf_response('Cash Flow', headers, rows, 'cash_flow.pdf')


class PartyStatementPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, party_id):
        try:
            data = get_party_statement_data(party_id)
        except Party.DoesNotExist:
            return Response({'error': 'Party not found.'}, status=status.HTTP_404_NOT_FOUND)
        headers = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
        rows = [[e['date'], e['description'], e['debit'], e['credit'], e['balance']] for e in data['entries']]
        rows.append(['', 'Opening Balance', '', '', data['opening_balance']])
        rows.append(['', 'Closing Balance', '', '', data['closing_balance']])
        return build_pdf_response(f'Party Statement: {data["party"]}', headers, rows, f'party_statement_{party_id}.pdf')
