from apps.accounts.models import User
from apps.fiscal.models import FiscalYear, FiscalPeriod
from apps.chart_of_accounts.models import Account
from apps.parties.models import Party
from apps.inventory.models import Product
from apps.currencies.models import Currency
from apps.cost_centers.models import CostCenter
from apps.sequences.models import DocumentSequence

admin = User.objects.get(username='admin')

# سنة مالية وفترة
fy, _ = FiscalYear.objects.get_or_create(name='2026', defaults={'start_date':'2026-01-01','end_date':'2026-12-31'})
period, _ = FiscalPeriod.objects.get_or_create(fiscal_year=fy, name='يناير 2026', defaults={'start_date':'2026-01-01','end_date':'2026-01-31'})

# حسابات
accounts = {}
account_defs = [
    {'code':'1001','name_ar':'الخزينة','name_en':'Cash','account_type':'Asset','normal_balance':'Debit'},
    {'code':'1101','name_ar':'العملاء','name_en':'Accounts Receivable','account_type':'Asset','normal_balance':'Debit'},
    {'code':'1401','name_ar':'المخزون','name_en':'Inventory','account_type':'Asset','normal_balance':'Debit'},
    {'code':'1501','name_ar':'مصروف الإهلاك','name_en':'Depreciation Expense','account_type':'Expense','normal_balance':'Debit'},
    {'code':'1601','name_ar':'مجمع الإهلاك','name_en':'Accumulated Depreciation','account_type':'Asset','normal_balance':'Credit'},
    {'code':'2001','name_ar':'الموردين','name_en':'Accounts Payable','account_type':'Liability','normal_balance':'Credit'},
    {'code':'3001','name_ar':'الأرباح المحتجزة','name_en':'Retained Earnings','account_type':'Equity','normal_balance':'Credit'},
    {'code':'4001','name_ar':'إيراد المبيعات','name_en':'Sales Revenue','account_type':'Revenue','normal_balance':'Credit'},
    {'code':'5001','name_ar':'تكلفة البضاعة المباعة','name_en':'Cost of Goods Sold','account_type':'Expense','normal_balance':'Debit'},
    {'code':'6001','name_ar':'رواتب','name_en':'Salaries Expense','account_type':'Expense','normal_balance':'Debit'},
]
for acc in account_defs:
    obj, _ = Account.objects.get_or_create(code=acc['code'], defaults={
        'name_ar': acc['name_ar'], 'name_en': acc['name_en'],
        'account_type': acc['account_type'], 'normal_balance': acc['normal_balance'],
        'allow_posting': True, 'is_active': True, 'created_by': admin
    })
    accounts[acc['code']] = obj

# عميل ومورد
customer, _ = Party.objects.get_or_create(name_ar='عميل اختبار', defaults={
    'name_en':'Test Customer', 'party_type':'Customer', 'default_account': accounts['1101'],
    'opening_balance':0, 'opening_balance_date':'2026-01-01'
})
supplier, _ = Party.objects.get_or_create(name_ar='مورد اختبار', defaults={
    'name_en':'Test Supplier', 'party_type':'Supplier', 'default_account': accounts['2001'],
    'opening_balance':0, 'opening_balance_date':'2026-01-01'
})

# منتج
product, _ = Product.objects.get_or_create(sku='TEST-PROD-001', defaults={
    'name_ar':'منتج اختبار', 'name_en':'Test Product', 'unit':'piece',
    'valuation_method':'Weighted Average', 'selling_price':100, 'average_cost':50,
    'reorder_level':0, 'inventory_account':accounts['1401'], 'cogs_account':accounts['5001'],
    'revenue_account': accounts['4001'],
})

# عملة
currency, _ = Currency.objects.get_or_create(code='USD', defaults={'name':'US Dollar', 'is_base_currency':False})

# مركز تكلفة
cost_center, _ = CostCenter.objects.get_or_create(code='CC1', defaults={'name_ar':'مركز تكلفة 1','name_en':'Cost Center 1','is_active':True})

# تعيين حساب الأرباح المحتجزة للسنة
fy.retained_earnings_account = accounts['3001']
fy.save()

print('Base data created')
