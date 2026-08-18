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
