from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from apps.invoicing.models import Invoice, InvoiceItem
from apps.payments.models import ReceiptPayment


def _make_invoice(base_data, customer, product, quantity=2, unit_price=100):
    invoice = Invoice.objects.create(
        invoice_type=Invoice.InvoiceType.SALE,
        fiscal_period=base_data['period'],
        date='2026-01-10',
        party=customer,
    )
    InvoiceItem.objects.create(
        invoice=invoice, product=product, quantity=quantity,
        unit_price=unit_price, unit_cost=product.average_cost,
    )
    invoice.update_totals()
    invoice.refresh_from_db()
    return invoice


def _make_receipt(base_data, customer, amount):
    return ReceiptPayment.objects.create(
        document_type=ReceiptPayment.DocumentType.RECEIPT,
        fiscal_period=base_data['period'], date='2026-01-10',
        party=customer, amount=amount,
        account=base_data['accounts']['cash'],
    )


@pytest.mark.django_db
def test_cannot_allocate_to_unposted_invoice(base_data, customer, product):
    invoice = _make_invoice(base_data, customer, product)
    rp = _make_receipt(base_data, customer, invoice.total_amount)

    with pytest.raises(ValidationError):
        rp.allocate_to_invoice(invoice, invoice.total_amount)

    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.DRAFT
    assert rp.total_allocated == 0


@pytest.mark.django_db
def test_cannot_post_receipt_with_unallocated_amount(base_data, customer, product, admin_user):
    invoice = _make_invoice(base_data, customer, product)
    invoice.post(user=admin_user)
    rp = _make_receipt(base_data, customer, invoice.total_amount)

    with pytest.raises(ValidationError):
        rp.post(user=admin_user)

    assert rp.journal_entry is None


@pytest.mark.django_db
def test_allocate_and_post_after_invoice_posted(base_data, customer, product, admin_user):
    invoice = _make_invoice(base_data, customer, product)
    invoice.post(user=admin_user)
    rp = _make_receipt(base_data, customer, invoice.total_amount)

    rp.allocate_to_invoice(invoice, invoice.total_amount)
    rp.post(user=admin_user)

    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.PAID
    assert invoice.paid_amount == invoice.total_amount
    assert rp.journal_entry is not None


@pytest.mark.django_db
def test_cannot_allocate_receipt_to_invoice_with_mismatched_currency(base_data, customer, product, admin_user):
    from apps.currencies.models import Currency

    Currency.objects.create(code='SDG', name='Sudanese Pound', is_base_currency=True)
    usd = Currency.objects.create(code='USD', name='US Dollar')

    invoice = _make_invoice(base_data, customer, product)  # بلا عملة = العملة الأساسية
    invoice.post(user=admin_user)

    rp = ReceiptPayment.objects.create(
        document_type=ReceiptPayment.DocumentType.RECEIPT,
        fiscal_period=base_data['period'], date='2026-01-10',
        party=customer, amount=100, account=base_data['accounts']['cash'],
        currency=usd, exchange_rate_used=Decimal('600'),
    )
    with pytest.raises(ValidationError):
        rp.allocate_to_invoice(invoice, invoice.total_amount)


@pytest.mark.django_db
def test_foreign_currency_receipt_converts_to_base_currency_on_posting(base_data, customer, product, admin_user):
    from apps.currencies.models import Currency, ExchangeRateHistory

    Currency.objects.create(code='SDG', name='Sudanese Pound', is_base_currency=True)
    usd = Currency.objects.create(code='USD', name='US Dollar')
    ExchangeRateHistory.objects.create(currency=usd, rate=Decimal('600'), date='2026-01-01')

    invoice = Invoice.objects.create(
        invoice_type=Invoice.InvoiceType.SALE, fiscal_period=base_data['period'],
        date='2026-01-10', party=customer, currency=usd,
    )
    InvoiceItem.objects.create(
        invoice=invoice, product=product, quantity=2, unit_price=100, unit_cost=product.average_cost,
    )
    invoice.update_totals()
    invoice.refresh_from_db()
    invoice.post(user=admin_user)

    # اشتقاق سعر الصرف التلقائي يحدث في الـ serializer (كما في الفواتير)،
    # وليس في هذا الإنشاء المباشر عبر ORM، فيُمرَّر صراحة هنا.
    rp = ReceiptPayment.objects.create(
        document_type=ReceiptPayment.DocumentType.RECEIPT,
        fiscal_period=base_data['period'], date='2026-01-10',
        party=customer, amount=200, account=base_data['accounts']['cash'],
        currency=usd, exchange_rate_used=Decimal('600'),
    )

    rp.allocate_to_invoice(invoice, 200)
    rp.post(user=admin_user)

    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.PAID

    je = rp.journal_entry
    cash_line = je.lines.get(account=base_data['accounts']['cash'])
    receivable_line = je.lines.get(account=base_data['accounts']['receivable'])
    assert cash_line.debit == Decimal('120000.00')  # 200 USD * 600
    assert receivable_line.credit == Decimal('120000.00')


@pytest.mark.django_db
def test_receipt_exchange_rate_auto_derived_via_api(api_client, admin_user, accountant_user, base_data, customer, product):
    from apps.currencies.models import Currency, ExchangeRateHistory

    Currency.objects.create(code='SDG', name='Sudanese Pound', is_base_currency=True)
    usd = Currency.objects.create(code='USD', name='US Dollar')
    ExchangeRateHistory.objects.create(currency=usd, rate=Decimal('600'), date='2026-01-01')

    invoice = Invoice.objects.create(
        invoice_type=Invoice.InvoiceType.SALE, fiscal_period=base_data['period'],
        date='2026-01-10', party=customer, currency=usd,
    )
    InvoiceItem.objects.create(
        invoice=invoice, product=product, quantity=1, unit_price=50, unit_cost=product.average_cost,
    )
    invoice.update_totals()
    invoice.refresh_from_db()
    invoice.post(user=admin_user)

    api_client.force_authenticate(user=accountant_user)
    resp = api_client.post('/api/payments/receipts-payments/', {
        'document_type': 'Receipt', 'fiscal_period': base_data['period'].id, 'date': '2026-01-10',
        'party': customer.id, 'amount': '50', 'account': base_data['accounts']['cash'].id,
        'currency': usd.id,
    }, format='json')
    assert resp.status_code == 201, resp.data
    assert resp.data['exchange_rate_used'] == '600.000000'
