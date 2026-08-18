import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.invoicing.models import Invoice, InvoiceItem
from apps.journal_entries.services import close_fiscal_period
from apps.journal_entries.models import JournalEntryLine


def _make_and_post_sale_invoice(base_data, customer, product, admin_user, quantity=2, unit_price=100):
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
    invoice.post(user=admin_user)
    invoice.refresh_from_db()
    return invoice


@pytest.mark.django_db
def test_close_fiscal_period_posts_net_income_to_retained_earnings(base_data, customer, product, admin_user):
    invoice = _make_and_post_sale_invoice(base_data, customer, product, admin_user, quantity=2, unit_price=100)
    # صافي الربح المتوقع = الإيراد (200) - تكلفة البضاعة المباعة (2 * 50 = 100)
    expected_net_income = invoice.subtotal - Decimal('100.00')

    period = base_data['period']
    retained = base_data['accounts']['retained']

    entry = close_fiscal_period(period.id, user=admin_user)

    assert entry.is_posted is True
    assert entry.total_debit == entry.total_credit

    retained_totals = JournalEntryLine.objects.filter(
        journal_entry=entry, account=retained
    ).aggregate(debit=Sum('debit'), credit=Sum('credit'))
    net_to_retained = (retained_totals['credit'] or 0) - (retained_totals['debit'] or 0)
    assert net_to_retained == expected_net_income

    period.refresh_from_db()
    assert period.is_closed is True

    period.fiscal_year.refresh_from_db()
    assert period.fiscal_year.is_closed is True


@pytest.mark.django_db
def test_cannot_close_already_closed_period(base_data, customer, product, admin_user):
    _make_and_post_sale_invoice(base_data, customer, product, admin_user)
    period = base_data['period']
    close_fiscal_period(period.id, user=admin_user)

    with pytest.raises(ValidationError):
        close_fiscal_period(period.id, user=admin_user)
