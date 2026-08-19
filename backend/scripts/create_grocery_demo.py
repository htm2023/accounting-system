# -*- coding: utf-8 -*-
"""
سيناريو تعليمي كامل: متجر بقالة صغير.
يوضّح الدورة المحاسبية الكاملة عبر منطق التطبيق الفعلي (post/allocate)
وليس إدخالًا مباشرًا في قاعدة البيانات، ليكون مطابقًا لما يحدث فعليًا
عند استخدام الواجهة أو الـ API.

الفترة المالية تبقى مفتوحة عمدًا بعد انتهاء السكربت، حتى يمكن الاستمرار
في إضافة عمليات جديدة أو تجربة إقفال الفترة يدويًا لاحقًا.
"""
from decimal import Decimal
from apps.accounts.models import User
from apps.fiscal.models import FiscalYear, FiscalPeriod
from apps.chart_of_accounts.models import Account
from apps.parties.models import Party
from apps.inventory.models import Product
from apps.invoicing.models import Invoice, InvoiceItem
from apps.payments.models import ReceiptPayment
from apps.journal_entries.services import create_journal_entry

admin = User.objects.filter(role='Admin').first()

fy = FiscalYear.objects.get(name='2026')
period = FiscalPeriod.objects.get(fiscal_year=fy, name='يناير 2026')

# ---------------------------------------------------------------------------
# 1) حسابات إضافية خاصة برأس المال والإيجار (البقية موجودة مسبقًا في الدليل)
# ---------------------------------------------------------------------------
def get_account(code):
    return Account.objects.get(code=code)

capital, _ = Account.objects.get_or_create(code='3002', defaults={
    'name_ar': 'رأس المال', 'name_en': "Owner's Capital",
    'account_type': 'Equity', 'normal_balance': 'Credit',
    'allow_posting': True, 'is_active': True, 'created_by': admin,
})
rent_expense, _ = Account.objects.get_or_create(code='6002', defaults={
    'name_ar': 'مصروف الإيجار', 'name_en': 'Rent Expense',
    'account_type': 'Expense', 'normal_balance': 'Debit',
    'allow_posting': True, 'is_active': True, 'created_by': admin,
})

cash = get_account('1001')
receivable = get_account('1101')
inventory_acc = get_account('1401')
payable = get_account('2001')
revenue = get_account('4001')
cogs = get_account('5001')
salaries = get_account('6001')

# ---------------------------------------------------------------------------
# 2) موردون وعملاء
# ---------------------------------------------------------------------------
supplier1, _ = Party.objects.get_or_create(name_ar='الوفاء للتوزيع الغذائي', defaults={
    'name_en': 'Al-Wafa Food Distribution', 'party_type': 'Supplier',
    'default_account': payable, 'opening_balance': 0, 'opening_balance_date': '2026-01-01',
})
supplier2, _ = Party.objects.get_or_create(name_ar='شركة النور للمواد الغذائية', defaults={
    'name_en': 'Al-Noor Foodstuff Co.', 'party_type': 'Supplier',
    'default_account': payable, 'opening_balance': 0, 'opening_balance_date': '2026-01-01',
})
walkin_customer, _ = Party.objects.get_or_create(name_ar='زبون نقدي', defaults={
    'name_en': 'Walk-in Customer', 'party_type': 'Customer',
    'default_account': receivable, 'opening_balance': 0, 'opening_balance_date': '2026-01-01',
})
restaurant_customer, _ = Party.objects.get_or_create(name_ar='مطعم الأصالة', defaults={
    'name_en': 'Al-Asala Restaurant', 'party_type': 'Customer',
    'default_account': receivable, 'opening_balance': 0, 'opening_balance_date': '2026-01-01',
})

# ---------------------------------------------------------------------------
# 3) منتجات بقالة واقعية
# ---------------------------------------------------------------------------
product_defs = [
    ('RICE-5KG', 'أرز (5 كجم)', 'Rice 5kg', 12, 18),
    ('SUGAR-1KG', 'سكر (1 كجم)', 'Sugar 1kg', 3, 4.5),
    ('OIL-1.5L', 'زيت طبخ (1.5 لتر)', 'Cooking Oil 1.5L', 8, 11),
    ('TEA-400G', 'شاي (400 جم)', 'Tea 400g', 5, 7.5),
    ('PASTA-500G', 'معكرونة (500 جم)', 'Pasta 500g', 2, 3),
    ('TOMATO-CAN', 'طماطم معلبة', 'Canned Tomatoes', 1.5, 2.5),
    ('WATER-1.5L', 'مياه معدنية (1.5 لتر)', 'Mineral Water 1.5L', Decimal('0.8'), 1.5),
]
products = {}
for sku, name_ar, name_en, cost, price in product_defs:
    p, _ = Product.objects.get_or_create(sku=sku, defaults={
        'name_ar': name_ar, 'name_en': name_en, 'unit': 'piece',
        'valuation_method': 'Weighted Average',
        'selling_price': price, 'average_cost': cost, 'reorder_level': 10,
        'inventory_account': inventory_acc, 'cogs_account': cogs,
        'revenue_account': revenue,
    })
    products[sku] = p

print('== الإعداد الأساسي جاهز: الحسابات، الأطراف، المنتجات ==')

# ---------------------------------------------------------------------------
# 4) رأس مال افتتاحي: الخزينة مدين / رأس المال دائن
# ---------------------------------------------------------------------------
opening_entry = create_journal_entry(
    fiscal_period=period, date='2026-01-02',
    description='رأس مال افتتاحي لصاحب المحل',
    lines_data=[
        {'account': cash, 'debit': 50000, 'credit': 0},
        {'account': capital, 'debit': 0, 'credit': 50000},
    ],
    created_by=admin, auto_post=True, approved_by=admin,
)
print('رأس المال الافتتاحي: قيد رقم', opening_entry.entry_number)


def make_invoice(invoice_type, date, party, items):
    """items: list of (sku, quantity, unit_price)"""
    invoice = Invoice.objects.create(
        invoice_type=invoice_type, fiscal_period=period, date=date, party=party,
    )
    for sku, qty, unit_price in items:
        product = products[sku]
        if invoice_type == Invoice.InvoiceType.SALE:
            product.refresh_from_db()  # متوسط التكلفة يتحدّث مع كل حركة شراء سابقة
        unit_cost = product.average_cost if invoice_type == Invoice.InvoiceType.SALE else unit_price
        InvoiceItem.objects.create(
            invoice=invoice, product=product, quantity=qty,
            unit_price=unit_price, unit_cost=unit_cost,
        )
    invoice.update_totals()
    invoice.refresh_from_db()
    invoice.post(user=admin)
    invoice.refresh_from_db()
    return invoice


# ---------------------------------------------------------------------------
# 5) فواتير شراء من الموردين (تزيد المخزون وتُنشئ التزامًا على المحل)
# ---------------------------------------------------------------------------
purchase1 = make_invoice(Invoice.InvoiceType.PURCHASE, '2026-01-03', supplier1, [
    ('RICE-5KG', 100, 12),
    ('SUGAR-1KG', 200, 3),
    ('OIL-1.5L', 80, 8),
    ('TEA-400G', 60, 5),
])
print('فاتورة شراء 1 من', supplier1.name_ar, '- الإجمالي', purchase1.total_amount, '- مرحّلة:', purchase1.status)

purchase2 = make_invoice(Invoice.InvoiceType.PURCHASE, '2026-01-04', supplier2, [
    ('PASTA-500G', 150, 2),
    ('TOMATO-CAN', 200, 1.5),
    ('WATER-1.5L', 300, Decimal('0.8')),
])
print('فاتورة شراء 2 من', supplier2.name_ar, '- الإجمالي', purchase2.total_amount, '- مرحّلة:', purchase2.status)

# ---------------------------------------------------------------------------
# 6) سداد كامل المستحق للمورد الأول
# ---------------------------------------------------------------------------
payment_to_supplier1 = ReceiptPayment.objects.create(
    document_type=ReceiptPayment.DocumentType.PAYMENT, fiscal_period=period,
    date='2026-01-08', party=supplier1, amount=purchase1.total_amount, account=cash,
    description='سداد مستحقات المورد الوفاء للتوزيع الغذائي',
)
payment_to_supplier1.allocate_to_invoice(purchase1, purchase1.total_amount)
payment_to_supplier1.post(user=admin)
purchase1.refresh_from_db()
print('سداد المورد 1:', payment_to_supplier1.number, '- حالة فاتورة الشراء بعد السداد:', purchase1.status)

# ---------------------------------------------------------------------------
# 7) مبيعات نقدية متكررة (زبون نقدي)
# ---------------------------------------------------------------------------
sale1 = make_invoice(Invoice.InvoiceType.SALE, '2026-01-05', walkin_customer, [
    ('RICE-5KG', 5, 18), ('SUGAR-1KG', 10, 4.5), ('OIL-1.5L', 3, 11),
])
sale2 = make_invoice(Invoice.InvoiceType.SALE, '2026-01-10', walkin_customer, [
    ('TEA-400G', 4, 7.5), ('PASTA-500G', 20, 3), ('TOMATO-CAN', 15, 2.5),
])
sale3 = make_invoice(Invoice.InvoiceType.SALE, '2026-01-15', walkin_customer, [
    ('WATER-1.5L', 50, 1.5), ('RICE-5KG', 3, 18),
])

# البيع لزبون نقدي يبقى فاتورة "Posted" غير مسددة حتى تُحصَّل فعليًا؛ بما أنها
# مبيعات نقدية فورية، نُنشئ سند قبض بنفس تاريخ كل فاتورة ونحصّله فورًا.
for sale in (sale1, sale2, sale3):
    receipt = ReceiptPayment.objects.create(
        document_type=ReceiptPayment.DocumentType.RECEIPT, fiscal_period=period,
        date=sale.date, party=walkin_customer, amount=sale.total_amount, account=cash,
        description=f'تحصيل نقدي فوري - فاتورة {sale.invoice_number}',
    )
    receipt.allocate_to_invoice(sale, sale.total_amount)
    receipt.post(user=admin)

print('مبيعات نقدية (محصّلة فورًا):', sale1.invoice_number, sale1.total_amount, '|',
      sale2.invoice_number, sale2.total_amount, '|', sale3.invoice_number, sale3.total_amount)

# ---------------------------------------------------------------------------
# 8) بيع آجل بالجملة لمطعم (يُنشئ حسابًا مدينًا Accounts Receivable)
# ---------------------------------------------------------------------------
wholesale_sale = make_invoice(Invoice.InvoiceType.SALE, '2026-01-12', restaurant_customer, [
    ('RICE-5KG', 20, 18), ('OIL-1.5L', 15, 11), ('PASTA-500G', 40, 3), ('TOMATO-CAN', 60, 2.5),
])
print('بيع آجل لـ', restaurant_customer.name_ar, '- الإجمالي', wholesale_sale.total_amount,
      '- حالة الفاتورة:', wholesale_sale.status)

# ---------------------------------------------------------------------------
# 9) تحصيل كامل المبلغ من المطعم
# ---------------------------------------------------------------------------
receipt_from_restaurant = ReceiptPayment.objects.create(
    document_type=ReceiptPayment.DocumentType.RECEIPT, fiscal_period=period,
    date='2026-01-20', party=restaurant_customer, amount=wholesale_sale.total_amount, account=cash,
    description='تحصيل مستحقات مطعم الأصالة',
)
receipt_from_restaurant.allocate_to_invoice(wholesale_sale, wholesale_sale.total_amount)
receipt_from_restaurant.post(user=admin)
wholesale_sale.refresh_from_db()
print('تحصيل من المطعم:', receipt_from_restaurant.number, '- حالة الفاتورة بعد التحصيل:', wholesale_sale.status)

# ---------------------------------------------------------------------------
# 10) مصروفات تشغيلية شهرية: إيجار ورواتب
# ---------------------------------------------------------------------------
rent_entry = create_journal_entry(
    fiscal_period=period, date='2026-01-31', description='إيجار محل البقالة - يناير 2026',
    lines_data=[
        {'account': rent_expense, 'debit': 3000, 'credit': 0},
        {'account': cash, 'debit': 0, 'credit': 3000},
    ],
    created_by=admin, auto_post=True, approved_by=admin,
)
salaries_entry = create_journal_entry(
    fiscal_period=period, date='2026-01-31', description='رواتب العاملين - يناير 2026',
    lines_data=[
        {'account': salaries, 'debit': 4000, 'credit': 0},
        {'account': cash, 'debit': 0, 'credit': 4000},
    ],
    created_by=admin, auto_post=True, approved_by=admin,
)
print('مصروف الإيجار: قيد', rent_entry.entry_number, '| مصروف الرواتب: قيد', salaries_entry.entry_number)

# ---------------------------------------------------------------------------
# ملخص نهائي
# ---------------------------------------------------------------------------
print('\n================ ملخص السيناريو ================')
print('الفترة المالية "يناير 2026" لا تزال مفتوحة عمدًا (لم تُقفل) لتتمكن من:')
print('  - إضافة فواتير/قيود جديدة والاستكشاف بحرية')
print('  - تجربة إقفال الفترة بنفسك لاحقًا (POST /api/journal-entries/close-period/<id>/)')
print('رصيد الخزينة = 50000 - 2740(دفعة مورد) + 424.5(مبيعات نقدية محصّلة) + 795(تحصيل من المطعم) - 7000(إيجار+رواتب) = 41479.5')
