import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.accounts.models import User
from apps.fiscal.models import FiscalYear, FiscalPeriod
from apps.chart_of_accounts.models import Account

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return User.objects.create_user(username='admin_test', password='password123', role='Admin')

@pytest.fixture
def accountant_user():
    return User.objects.create_user(username='accountant_test', password='password123', role='Accountant')

@pytest.fixture
def base_data(admin_user):
    fy = FiscalYear.objects.create(name='2026', start_date='2026-01-01', end_date='2026-12-31')
    period = FiscalPeriod.objects.create(
        fiscal_year=fy, name='Jan 2026',
        start_date='2026-01-01', end_date='2026-01-31'
    )
    accounts = {}
    defs = [
        ('cash', 'Cash', 'Asset', 'Debit'),
        ('receivable', 'Accounts Receivable', 'Asset', 'Debit'),
        ('inventory', 'Inventory', 'Asset', 'Debit'),
        ('payable', 'Accounts Payable', 'Liability', 'Credit'),
        ('revenue', 'Sales Revenue', 'Revenue', 'Credit'),
        ('cogs', 'COGS', 'Expense', 'Debit'),
        ('retained', 'Retained Earnings', 'Equity', 'Credit'),
        ('dep_expense', 'Depreciation Expense', 'Expense', 'Debit'),
        ('acc_dep', 'Accumulated Depreciation', 'Asset', 'Credit'),
    ]
    for code, name, type, balance in defs:
        acc = Account.objects.create(
            code=code.upper()[:20], name_ar=name, name_en=name,
            account_type=type, normal_balance=balance,
            allow_posting=True, is_active=True, created_by=admin_user
        )
        accounts[code] = acc
    fy.retained_earnings_account = accounts['retained']
    fy.save()
    return {
        'fy': fy,
        'period': period,
        'accounts': accounts,
    }

@pytest.fixture
def product(base_data):
    from apps.inventory.models import Product
    return Product.objects.create(
        sku='TEST-PROD', name_ar='Test Product', name_en='Test Product',
        unit='piece', valuation_method='Weighted Average',
        selling_price=100, average_cost=50,
        reorder_level=0,
        inventory_account=base_data['accounts']['inventory'],
        cogs_account=base_data['accounts']['cogs'],
        revenue_account=base_data['accounts']['revenue'],
    )

@pytest.fixture
def customer(base_data):
    from apps.parties.models import Party
    return Party.objects.create(
        party_type='Customer', name_ar='Test Customer', name_en='Test Customer',
        default_account=base_data['accounts']['receivable'],
        opening_balance=0, opening_balance_date='2026-01-01'
    )
