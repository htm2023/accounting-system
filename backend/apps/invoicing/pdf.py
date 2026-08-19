from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from apps.currencies.models import Currency

def _base_currency_code():
    base = Currency.objects.filter(is_base_currency=True).first()
    return base.code if base else ''

# تسجيل الخط العربي مرة واحدة
def register_arabic_font():
    try:
        pdfmetrics.registerFont(TTFont('Arabic', r'C:\Windows\Fonts\arialuni.ttf'))
        return 'Arabic'
    except:
        return 'Helvetica'

ARABIC_FONT = register_arabic_font()

def ar(text):
    """تحويل النص العربي لشكل مناسب للـ PDF"""
    if text:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    return ''

def invoice_to_pdf(invoice):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=15*mm)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, fontName=ARABIC_FONT, fontSize=18, leading=24)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Heading2'], alignment=1, fontName=ARABIC_FONT, fontSize=14, leading=20)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=ARABIC_FONT, fontSize=11, leading=16, alignment=1)
    left_style = ParagraphStyle('LeftStyle', parent=styles['Normal'], fontName=ARABIC_FONT, fontSize=11, leading=16, alignment=0)

    # عنوان الفاتورة
    elements.append(Paragraph(ar('فاتورة'), title_style))
    elements.append(Paragraph(ar(f"نوع: {'بيع' if invoice.invoice_type == 'Sale' else 'شراء'}"), subtitle_style))
    elements.append(Spacer(1, 5*mm))

    # بيانات أساسية
    currency_code = invoice.currency.code if invoice.currency else _base_currency_code()
    data = [
        [Paragraph(ar('رقم الفاتورة'), left_style), Paragraph(invoice.invoice_number, left_style)],
        [Paragraph(ar('التاريخ'), left_style), Paragraph(str(invoice.date), left_style)],
        [Paragraph(ar('تاريخ الاستحقاق'), left_style), Paragraph(str(invoice.due_date) if invoice.due_date else '-', left_style)],
        [Paragraph(ar('الطرف'), left_style), Paragraph(ar(invoice.party.name_ar or invoice.party.name_en), left_style)],
        [Paragraph(ar('الحالة'), left_style), Paragraph(invoice.status, left_style)],
        [Paragraph(ar('العملة'), left_style), Paragraph(currency_code, left_style)],
    ]
    if invoice.currency and not invoice.currency.is_base_currency:
        data.append([Paragraph(ar('سعر الصرف'), left_style), Paragraph(str(invoice.exchange_rate_used), left_style)])
    info_table = Table(data, colWidths=[50*mm, 80*mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # جدول الأصناف
    headers = [Paragraph(ar('المنتج'), left_style), Paragraph(ar('الكمية'), left_style), Paragraph(ar('سعر الوحدة'), left_style), Paragraph(ar('الضريبة %'), left_style), Paragraph(ar('الخصم'), left_style), Paragraph(ar('الإجمالي'), left_style)]
    items_data = [headers]
    for item in invoice.items.all():
        items_data.append([
            Paragraph(ar(item.product.name_ar or item.product.name_en), left_style),
            Paragraph(str(item.quantity), left_style),
            Paragraph(str(item.unit_price), left_style),
            Paragraph(str(item.tax_rate), left_style),
            Paragraph(str(item.discount), left_style),
            Paragraph(str(item.total), left_style),
        ])

    items_table = Table(items_data, repeatRows=1, colWidths=[45*mm, 20*mm, 25*mm, 20*mm, 20*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), ARABIC_FONT),
        ('FONTNAME', (0,1), (-1,-1), ARABIC_FONT),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 8*mm))

    # إجماليات
    totals_data = [
        [Paragraph(ar('الإجمالي الفرعي'), left_style), Paragraph(str(invoice.subtotal), left_style)],
        [Paragraph(ar('الضريبة'), left_style), Paragraph(str(invoice.tax_amount), left_style)],
        [Paragraph(ar('الخصم'), left_style), Paragraph(str(invoice.discount), left_style)],
        [Paragraph(ar('الإجمالي النهائي'), left_style), Paragraph(str(invoice.total_amount), left_style)],
        [Paragraph(ar('المدفوع'), left_style), Paragraph(str(invoice.paid_amount), left_style)],
        [Paragraph(ar('المتبقي'), left_style), Paragraph(str(invoice.total_amount - invoice.paid_amount), left_style)],
    ]
    totals_table = Table(totals_data, colWidths=[70*mm, 60*mm])
    totals_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,3), (-1,3), colors.whitesmoke),
        ('FONTNAME', (0,3), (-1,3), ARABIC_FONT),
    ]))
    elements.append(totals_table)

    doc.build(elements)
    return response
