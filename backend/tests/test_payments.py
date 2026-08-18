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
