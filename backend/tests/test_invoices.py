import pytest
from decimal import Decimal
from apps.invoicing.models import Invoice
from apps.inventory.models import Product, StockMovement

INVOICES_URL = '/api/invoicing/invoices/'


def _post_url(invoice_id):
    return f'{INVOICES_URL}{invoice_id}/post/'


def _create_invoice(api_client, user, base_data, customer, product_id, quantity=2, unit_price=100):
    api_client.force_authenticate(user=user)
    return api_client.post(INVOICES_URL, {
        'invoice_type': 'Sale',
        'fiscal_period': base_data['period'].id,
        'date': '2026-01-10',
        'party': customer.id,
        'items': [{'product': product_id, 'quantity': quantity, 'unit_price': unit_price}],
    }, format='json')


@pytest.mark.django_db
def test_cannot_post_invoice_without_revenue_account(api_client, admin_user, accountant_user, base_data, customer):
    # منتج بدون revenue_account (اختياري في الموديل) — يجب أن يُرفض الترحيل
    product_no_revenue = Product.objects.create(
        sku='NO-REV-PROD', name_ar='منتج بدون إيراد', name_en='No Revenue Product',
        unit='piece', valuation_method='Weighted Average',
        selling_price=100, average_cost=50, reorder_level=0,
        inventory_account=base_data['accounts']['inventory'],
        cogs_account=base_data['accounts']['cogs'],
    )
    resp = _create_invoice(api_client, accountant_user, base_data, customer, product_no_revenue.id)
    assert resp.status_code == 201, resp.data
    invoice_id = resp.data['id']

    api_client.force_authenticate(user=admin_user)
    resp = api_client.post(_post_url(invoice_id))
    assert resp.status_code == 400, resp.data
    assert 'revenue_account' in str(resp.data)

    invoice = Invoice.objects.get(id=invoice_id)
    assert invoice.status == Invoice.Status.DRAFT
    assert invoice.journal_entry is None


@pytest.mark.django_db
def test_post_sale_invoice_creates_negative_stock_movement(api_client, admin_user, accountant_user, base_data, product, customer):
    resp = _create_invoice(api_client, accountant_user, base_data, customer, product.id, quantity=3)
    assert resp.status_code == 201, resp.data
    invoice_id = resp.data['id']

    api_client.force_authenticate(user=admin_user)
    resp = api_client.post(_post_url(invoice_id))
    assert resp.status_code == 200, resp.data

    invoice = Invoice.objects.get(id=invoice_id)
    assert invoice.status == Invoice.Status.POSTED
    assert invoice.journal_entry is not None

    movement = StockMovement.objects.get(reference_type='Invoice', reference_id=str(invoice_id))
    assert movement.movement_type == StockMovement.MovementType.SALE
    assert movement.quantity == Decimal('-3.00')


@pytest.mark.django_db
def test_cannot_edit_posted_invoice(api_client, admin_user, accountant_user, base_data, product, customer):
    resp = _create_invoice(api_client, accountant_user, base_data, customer, product.id, quantity=1)
    assert resp.status_code == 201, resp.data
    invoice_id = resp.data['id']

    api_client.force_authenticate(user=admin_user)
    resp = api_client.post(_post_url(invoice_id))
    assert resp.status_code == 200, resp.data

    api_client.force_authenticate(user=accountant_user)
    resp = api_client.put(f'{INVOICES_URL}{invoice_id}/', {
        'invoice_type': 'Sale',
        'fiscal_period': base_data['period'].id,
        'date': '2026-01-11',
        'party': customer.id,
        'items': [{'product': product.id, 'quantity': 5, 'unit_price': 100}],
    }, format='json')
    assert resp.status_code == 400, resp.data
    assert 'Only draft invoices can be modified.' in str(resp.data)


@pytest.mark.django_db
def test_can_allocate_payment_to_invoice_after_its_period_closes(api_client, admin_user, accountant_user, base_data, product, customer):
    from apps.payments.models import ReceiptPayment
    from apps.fiscal.models import FiscalPeriod

    resp = _create_invoice(api_client, accountant_user, base_data, customer, product.id, quantity=1, unit_price=200)
    assert resp.status_code == 201, resp.data
    invoice_id = resp.data['id']

    api_client.force_authenticate(user=admin_user)
    resp = api_client.post(_post_url(invoice_id))
    assert resp.status_code == 200, resp.data

    # إقفال فترة الفاتورة، ثم تحصيلها لاحقًا عبر سند بتاريخ فترة تالية مفتوحة
    # (محاكاة سيناريو واقعي: فاتورة رُحّلت ثم أُقفلت فترتها قبل أن يسدد العميل).
    from apps.journal_entries.services import close_fiscal_period
    close_fiscal_period(base_data['period'].id, user=admin_user)

    period = base_data['period']
    period.refresh_from_db()
    assert period.is_closed

    period2 = FiscalPeriod.objects.create(
        fiscal_year=base_data['fy'], name='Feb 2026',
        start_date='2026-02-01', end_date='2026-02-28'
    )
    receipt = ReceiptPayment.objects.create(
        document_type=ReceiptPayment.DocumentType.RECEIPT, fiscal_period=period2,
        date='2026-02-05', party=customer, amount=200, account=base_data['accounts']['cash'],
    )
    invoice = Invoice.objects.get(id=invoice_id)
    # قبل الإصلاح: كان هذا يفشل بخطأ "Cannot create invoice in a closed
    # fiscal period." رغم أن الفاتورة نفسها ليست ما يُنشأ من جديد، بل تُحدَّث
    # تحديثًا محصورًا بـ paid_amount/status فقط.
    receipt.allocate_to_invoice(invoice, 200)
    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.PAID


@pytest.mark.django_db
def test_sale_and_purchase_invoice_numbers_do_not_collide(api_client, accountant_user, base_data, product, customer):
    from apps.parties.models import Party

    supplier = Party.objects.create(
        party_type='Supplier', name_ar='Test Supplier', name_en='Test Supplier',
        default_account=base_data['accounts']['payable'],
        opening_balance=0, opening_balance_date='2026-01-01'
    )
    api_client.force_authenticate(user=accountant_user)
    sale_resp = _create_invoice(api_client, accountant_user, base_data, customer, product.id)
    assert sale_resp.status_code == 201, sale_resp.data

    purchase_resp = api_client.post(INVOICES_URL, {
        'invoice_type': 'Purchase',
        'fiscal_period': base_data['period'].id,
        'date': '2026-01-10',
        'party': supplier.id,
        'items': [{'product': product.id, 'quantity': 1, 'unit_price': 10}],
    }, format='json')
    assert purchase_resp.status_code == 201, purchase_resp.data
    # قبل الإصلاح: كلا التسلسلين (بيع/شراء) يبدآن من "1" بلا بادئة مميزة،
    # فيتصادمان على invoice_number الفريد عالميًا.
    assert sale_resp.data['invoice_number'] != purchase_resp.data['invoice_number']


@pytest.mark.django_db
def test_foreign_currency_sale_converts_to_base_currency_on_posting(api_client, admin_user, accountant_user, base_data, product, customer):
    from apps.currencies.models import Currency, ExchangeRateHistory

    Currency.objects.create(code='SDG', name='Sudanese Pound', is_base_currency=True)
    usd = Currency.objects.create(code='USD', name='US Dollar')
    ExchangeRateHistory.objects.create(currency=usd, rate=Decimal('600'), date='2026-01-01')

    api_client.force_authenticate(user=accountant_user)
    resp = api_client.post(INVOICES_URL, {
        'invoice_type': 'Sale',
        'fiscal_period': base_data['period'].id,
        'date': '2026-01-10',
        'party': customer.id,
        'currency': usd.id,
        'items': [{'product': product.id, 'quantity': 2, 'unit_price': 100}],
    }, format='json')
    assert resp.status_code == 201, resp.data
    invoice_id = resp.data['id']

    invoice = Invoice.objects.get(id=invoice_id)
    # سعر الصرف يُشتق تلقائيًا من آخر سعر مسجَّل، والمبالغ المخزّنة على الفاتورة
    # تبقى بعملة الفاتورة نفسها (USD) للعرض/الطباعة.
    assert invoice.exchange_rate_used == Decimal('600')
    assert invoice.total_amount == Decimal('200.00')

    api_client.force_authenticate(user=admin_user)
    resp = api_client.post(_post_url(invoice_id))
    assert resp.status_code == 200, resp.data

    invoice.refresh_from_db()
    je = invoice.journal_entry
    party_line = je.lines.get(account=base_data['accounts']['receivable'])
    assert party_line.debit == Decimal('120000.00')  # 200 USD * 600
    revenue_line = je.lines.get(account=base_data['accounts']['revenue'])
    assert revenue_line.credit == Decimal('120000.00')

    total_debit = sum((l.debit for l in je.lines.all()), Decimal('0'))
    total_credit = sum((l.credit for l in je.lines.all()), Decimal('0'))
    assert total_debit == total_credit


@pytest.mark.django_db
def test_foreign_currency_purchase_converts_cost_to_base_currency(api_client, admin_user, accountant_user, base_data, product):
    from apps.currencies.models import Currency, ExchangeRateHistory
    from apps.parties.models import Party

    Currency.objects.create(code='SDG', name='Sudanese Pound', is_base_currency=True)
    usd = Currency.objects.create(code='USD', name='US Dollar')
    ExchangeRateHistory.objects.create(currency=usd, rate=Decimal('600'), date='2026-01-01')

    supplier = Party.objects.create(
        party_type='Supplier', name_ar='Test Supplier', name_en='Test Supplier',
        default_account=base_data['accounts']['payable'],
        opening_balance=0, opening_balance_date='2026-01-01'
    )

    api_client.force_authenticate(user=accountant_user)
    resp = api_client.post(INVOICES_URL, {
        'invoice_type': 'Purchase',
        'fiscal_period': base_data['period'].id,
        'date': '2026-01-10',
        'party': supplier.id,
        'currency': usd.id,
        'items': [{'product': product.id, 'quantity': 10, 'unit_price': 5}],
    }, format='json')
    assert resp.status_code == 201, resp.data
    invoice_id = resp.data['id']

    invoice = Invoice.objects.get(id=invoice_id)
    item = invoice.items.first()
    # unit_cost يُحوَّل فورًا للعملة الأساسية (5 USD * 600 = 3000)، حتى يبقى
    # تقييم المخزون ومتوسط التكلفة بعملة واحدة موحّدة.
    assert item.unit_cost == Decimal('3000.0000')

    api_client.force_authenticate(user=admin_user)
    resp = api_client.post(_post_url(invoice_id))
    assert resp.status_code == 200, resp.data

    invoice.refresh_from_db()
    je = invoice.journal_entry
    inventory_line = je.lines.get(account=base_data['accounts']['inventory'])
    payable_line = je.lines.get(account=base_data['accounts']['payable'])
    assert inventory_line.debit == Decimal('30000.00')  # 50 USD * 600
    assert payable_line.credit == Decimal('30000.00')

    product.refresh_from_db()
    assert product.average_cost == Decimal('3000.0000')
