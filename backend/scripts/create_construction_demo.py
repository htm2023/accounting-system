# -*- coding: utf-8 -*-
"""
سيناريو تعليمي كامل: شركة مقاولات وإنشاءات (شركة الأفق للمقاولات والإنشاءات).

يوضّح الدورة المحاسبية الكاملة عبر الـ REST API الفعلي (وليس إدخالًا مباشرًا
في قاعدة البيانات)، بنفس الأدوار والصلاحيات التي تُستخدم من الواجهة:
- محاسب (Accountant): ينشئ المستندات (فواتير، سندات، قيود، أصول...).
- مدير (Admin): يرحّل ويقفل الفترات.

يمر السيناريو على كل شاشة تقريبًا من القائمة الجانبية:
دليل الحسابات → مراكز التكلفة → العملات → الأطراف → المخزون → الموظفون
ومسيرات الرواتب → الأصول الثابتة وجداول الإهلاك → الفواتير → القيود
المحاسبية → سندات القبض والصرف → إقفال الفترة → التقارير → سجل العمليات.

ملاحظة منهجية مهمة: هذا النظام لا يملك وحدة "أعمال تحت التنفيذ" (WIP) أو
فوترة نسبة الإنجاز كما في أنظمة المقاولات المتخصصة. لذلك مُثّلت "دفعات
الإنجاز" (Progress Billing) كمنتجات فوترة (Sale) برمز خاص، ومُثّل تكلفة
مقاولي الباطن كفاتورة شراء (Purchase) لخدمة بدل سلعة. هذا حل عملي وليس
حلاً مثاليًا — يُذكر صراحة هنا حتى لا يُفهم على أنه تمثيل دقيق لمحاسبة
نسبة الإنجاز.

الفترة الثانية (فبراير 2026) تبقى مفتوحة عمدًا في نهاية السكربت.
"""
import os
import sys
import io
import django

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')  # عميل الاختبار الداخلي فقط لهذا السكربت

from decimal import Decimal
from rest_framework.test import APIClient
from apps.accounts.models import User

admin = User.objects.get(username='admin')
accountant = User.objects.get(username='accountant1')
client = APIClient()

STEP = [0]


def as_admin():
    client.force_authenticate(user=admin)


def as_accountant():
    client.force_authenticate(user=accountant)


def call(method, url, data=None, expect=(200, 201)):
    fn = getattr(client, method)
    resp = fn(url, data, format='json') if data is not None else fn(url)
    if resp.status_code not in expect:
        detail = getattr(resp, 'data', getattr(resp, 'content', b''))
        raise RuntimeError(f"FAILED {method.upper()} {url} [{resp.status_code}]: {detail}")
    return resp.data


def step(title):
    STEP[0] += 1
    print(f"\n[{STEP[0]}] {title}")


def ok(msg):
    print(f"    OK - {msg}")


# ===========================================================================
# 1) السنة المالية والفترات
# ===========================================================================
step("السنة المالية والفترات المحاسبية")
as_admin()
fy = call('post', '/api/fiscal/years/', {
    'name': '2026', 'start_date': '2026-01-01', 'end_date': '2026-12-31',
})
ok(f"سنة مالية {fy['name']} (id={fy['id']})")

as_accountant()
period1 = call('post', '/api/fiscal/periods/', {
    'fiscal_year': fy['id'], 'name': 'يناير 2026',
    'start_date': '2026-01-01', 'end_date': '2026-01-31',
})
period2 = call('post', '/api/fiscal/periods/', {
    'fiscal_year': fy['id'], 'name': 'فبراير 2026',
    'start_date': '2026-02-01', 'end_date': '2026-02-28',
})
ok(f"فترتان: {period1['name']}, {period2['name']}")


def period_for(date_str):
    return period2['id'] if date_str >= '2026-02-01' else period1['id']

# ===========================================================================
# 2) دليل الحسابات
# ===========================================================================
step("دليل الحسابات")
ACCOUNTS = [
    ('1001', 'الصندوق (نقدية)', 'Cash on Hand', 'Asset', 'Debit', True),
    ('1002', 'البنك', 'Bank', 'Asset', 'Debit', True),
    ('1003', 'عملاء عقود المقاولات', 'Contract Clients', 'Asset', 'Debit', False),
    ('1004', 'محتجزات مستحقة لدى العملاء', 'Retention Receivable', 'Asset', 'Debit', False),
    ('1005', 'مخزون مواد البناء', 'Materials Inventory', 'Asset', 'Debit', False),
    ('1006', 'أعمال تحت التنفيذ (غير مفوترة)', 'WIP - Uninvoiced Work', 'Asset', 'Debit', False),
    ('1007', 'المعدات والآليات', 'Equipment & Machinery', 'Asset', 'Debit', False),
    ('1008', 'مجمع إهلاك المعدات والآليات', 'Accum. Depreciation - Equipment', 'Asset', 'Credit', False),
    ('2001', 'موردو مواد البناء', 'Materials Suppliers Payable', 'Liability', 'Credit', False),
    ('2002', 'مقاولو الباطن (دائنون)', 'Subcontractors Payable', 'Liability', 'Credit', False),
    ('3001', 'رأس المال', "Owner's Capital", 'Equity', 'Credit', False),
    ('3002', 'الأرباح المحتجزة', 'Retained Earnings', 'Equity', 'Credit', False),
    ('4001', 'إيرادات عقود المقاولات', 'Contract Revenue', 'Revenue', 'Credit', False),
    ('5001', 'تكلفة مواد مستهلكة بالمشاريع', 'Direct Materials Cost', 'Expense', 'Debit', False),
    ('5002', 'تكلفة مقاولي الباطن', 'Subcontractor Costs', 'Expense', 'Debit', False),
    ('5003', 'أجور عمالة الموقع', 'Site Labor Wages', 'Expense', 'Debit', False),
    ('5004', 'مصروف إهلاك المعدات', 'Depreciation Expense - Equipment', 'Expense', 'Debit', False),
    ('5005', 'رواتب إدارية', 'Administrative Salaries', 'Expense', 'Debit', False),
    ('5006', 'مصاريف إدارية عمومية', 'General Overhead', 'Expense', 'Debit', False),
    ('5007', 'تكلفة الأعمال المنجزة المعترف بها', 'Cost of Contract Work Recognized', 'Expense', 'Debit', False),
]
acc = {}
as_accountant()
for code, name_ar, name_en, atype, normal, is_cash in ACCOUNTS:
    data = call('post', '/api/chart-of-accounts/accounts/', {
        'code': code, 'name_ar': name_ar, 'name_en': name_en,
        'account_type': atype, 'normal_balance': normal,
        'is_active': True, 'allow_posting': True,
    })
    acc[code] = data['id']
    # is_cash_account ليس في AccountSerializer الحالي (لا يُكتب عبر الـ API) لذلك يُترك افتراضيًا False.
ok(f"{len(acc)} حساب تم إنشاؤها")

# ربط حساب الأرباح المحتجزة بالسنة المالية بعد إنشاء دليل الحسابات
as_admin()
call('patch', f"/api/fiscal/years/{fy['id']}/", {'retained_earnings_account': acc['3002']})
ok('تم تعيين حساب الأرباح المحتجزة للسنة المالية')

# ===========================================================================
# 3) مراكز التكلفة (مشاريع)
# ===========================================================================
step("مراكز التكلفة")
as_accountant()
cc = {}
for code, name_ar, name_en in [
    ('CC-VILLA', 'مشروع فيلا سكنية - حي الرياض', 'Villa Project - Al-Riyadh Dist.'),
    ('CC-ROAD', 'مشروع رصف طريق - الأمانة', 'Road Paving Project'),
    ('CC-ADMIN', 'الإدارة العامة والمكتب الرئيسي', 'General Admin & Head Office'),
]:
    data = call('post', '/api/cost-centers/cost-centers/', {
        'code': code, 'name_ar': name_ar, 'name_en': name_en, 'is_active': True,
    })
    cc[code] = data['id']
ok(f"{len(cc)} مراكز تكلفة")

# ===========================================================================
# 4) العملات وأسعار الصرف
# ===========================================================================
step("العملات وأسعار الصرف")
sdg = call('post', '/api/currencies/currencies/', {
    'code': 'SDG', 'name': 'جنيه سوداني', 'is_base_currency': True,
})
usd = call('post', '/api/currencies/currencies/', {
    'code': 'USD', 'name': 'دولار أمريكي', 'is_base_currency': False,
})
call('post', '/api/currencies/exchange-rates/', {
    'currency': usd['id'], 'rate': '600.000000', 'date': '2026-01-01',
})
ok('SDG أساسية، USD بسعر صرف 600 بتاريخ 2026-01-01')

# ===========================================================================
# 5) الأطراف (عملاء / موردون / مقاولو باطن)
# ===========================================================================
step("الأطراف")
parties = {}
PARTIES = [
    ('client_villa', 'Customer', 'شركة النور العقارية', 'Al-Nour Real Estate', acc['1003']),
    ('client_road', 'Customer', 'أمانة الطرق والجسور', 'Roads & Bridges Authority', acc['1003']),
    ('supplier_local', 'Supplier', 'مؤسسة الخليج لمواد البناء', 'Gulf Building Materials Est.', acc['2001']),
    ('supplier_import', 'Supplier', 'شركة الاستيراد للمعدات والمواد', 'Import Co. for Equipment & Materials', acc['2001']),
    ('sub_elec', 'Supplier', 'مقاول الأعمال الكهربائية', 'Electrical Subcontractor', acc['2002']),
    ('sub_plumb', 'Supplier', 'مقاول أعمال السباكة', 'Plumbing Subcontractor', acc['2002']),
]
for key, ptype, name_ar, name_en, default_acc in PARTIES:
    data = call('post', '/api/parties/parties/', {
        'party_type': ptype, 'name_ar': name_ar, 'name_en': name_en,
        'default_account': default_acc, 'opening_balance': '0',
    })
    parties[key] = data['id']
ok(f"{len(parties)} أطراف (عميلان، موردان، مقاولا باطن)")

# ===========================================================================
# 6) المنتجات (مواد + خدمات مقاولي باطن + دفعات إنجاز)
# ===========================================================================
step("المنتجات (مواد البناء، خدمات الباطن، دفعات الإنجاز)")
products = {}
PRODUCTS = [
    # key, sku, name_ar, unit, inventory_account, cogs_account, revenue_account, selling_price
    ('cement', 'CEMENT-50', 'أسمنت بورتلاندي (كيس 50كغ)', 'كيس', acc['1005'], acc['5001'], None, '0'),
    ('sand', 'SAND-M3', 'رمل بناء', 'م3', acc['1005'], acc['5001'], None, '0'),
    ('rebar', 'REBAR-T12', 'حديد تسليح 12مم (مستورد)', 'طن', acc['1005'], acc['5001'], None, '0'),
    ('sub_elec_svc', 'SUB-ELEC', 'أعمال كهربائية - مقاول باطن', 'عقد', acc['5002'], acc['5002'], None, '0'),
    ('sub_plumb_svc', 'SUB-PLUMB', 'أعمال سباكة - مقاول باطن', 'عقد', acc['5002'], acc['5002'], None, '0'),
    ('ms_villa1', 'MS-VILLA-1', 'دفعة أعمال الأساسات - مشروع الفيلا', 'دفعة', acc['1006'], acc['5007'], acc['4001'], '800000'),
    ('ms_road1', 'MS-ROAD-1', 'دفعة أعمال الطبقة الأساسية - مشروع الطريق', 'دفعة', acc['1006'], acc['5007'], acc['4001'], '1200000'),
]
for key, sku, name_ar, unit, inv_acc, cogs_acc, rev_acc, price in PRODUCTS:
    payload = {
        'sku': sku, 'name_ar': name_ar, 'unit': unit,
        'valuation_method': 'Weighted Average',
        'selling_price': price, 'reorder_level': '0',
        'inventory_account': inv_acc, 'cogs_account': cogs_acc,
    }
    if rev_acc:
        payload['revenue_account'] = rev_acc
    data = call('post', '/api/inventory/products/', payload)
    products[key] = data['id']
ok(f"{len(products)} منتجات/خدمات")

# average_cost حقل للقراءة فقط عبر الـ API (يُحدَّث تلقائيًا من حركات المخزون
# فقط). دفعات الإنجاز ليست سلعًا حقيقية، فنمنحها تكلفة افتتاحية عبر حركة
# مخزون "رصيد افتتاحي" حقيقية عبر الـ API — بدل التحايل المباشر على قاعدة
# البيانات — حتى تُحتسب تكلفة الأعمال المعترف بها (5007) بشكل غير صفري
# عند البيع، بدلًا من ترك القيد بسطر صفري (وهو ما يرفضه النظام أصلًا).
call('post', '/api/inventory/stock-movements/', {
    'product': products['ms_villa1'], 'movement_type': 'Opening',
    'quantity': '1', 'unit_cost': '550000', 'date': '2026-01-01',
})
call('post', '/api/inventory/stock-movements/', {
    'product': products['ms_road1'], 'movement_type': 'Opening',
    'quantity': '1', 'unit_cost': '850000', 'date': '2026-01-01',
})
ok('تكلفة افتتاحية لدفعتي الإنجاز عبر حركة مخزون Opening')

# ===========================================================================
# 7) الموظفون
# ===========================================================================
step("الموظفون")
employees = {}
EMPLOYEES = [
    ('engineer', 'م. أحمد الطيب - مهندس موقع', 'مهندس موقع', '15000', '2025-06-01', acc['5003'], acc['1002']),
    ('worker', 'محمد آدم - عامل بناء', 'عامل بناء', '6000', '2025-09-01', acc['5003'], acc['1001']),
    ('accountant_emp', 'سارة عثمان - محاسبة إدارية', 'محاسب إداري', '10000', '2025-03-01', acc['5005'], acc['1002']),
]
for key, name, position, salary, hire_date, salary_acc, payment_acc in EMPLOYEES:
    data = call('post', '/api/payroll/employees/', {
        'name': name, 'position': position, 'basic_salary': salary,
        'hire_date': hire_date, 'status': 'Active',
        'salary_account': salary_acc, 'payment_account': payment_acc,
    })
    employees[key] = data['id']
ok(f"{len(employees)} موظفين")

# ===========================================================================
# 8) الأصول الثابتة وجداول الإهلاك
# ===========================================================================
step("الأصول الثابتة")
excavator = call('post', '/api/fixed-assets/assets/', {
    'name': 'حفارة هيدروليكية', 'asset_account': acc['1007'],
    'depreciation_account': acc['1008'], 'expense_account': acc['5004'],
    'purchase_date': '2026-01-05', 'cost': '1200000', 'salvage_value': '100000',
    'useful_life_years': 10, 'depreciation_method': 'Straight-line', 'status': 'Active',
})
mixer = call('post', '/api/fixed-assets/assets/', {
    'name': 'خلاطة خرسانة', 'asset_account': acc['1007'],
    'depreciation_account': acc['1008'], 'expense_account': acc['5004'],
    'purchase_date': '2026-01-05', 'cost': '300000', 'salvage_value': '20000',
    'useful_life_years': 6, 'depreciation_method': 'Straight-line', 'status': 'Active',
})
ok(f"أصلان: {excavator['name']}, {mixer['name']}")

# توليد جدول الإهلاك المبدئي: دالة نموذج بدون إجراء REST مخصص، فتُستدعى
# مباشرة عبر ORM (وليس تحايلًا على الـ API - هذا الإجراء غير مُعرَّض أصلًا).
from apps.fixed_assets.models import FixedAsset

FixedAsset.objects.get(id=excavator['id']).generate_depreciation_schedule()
FixedAsset.objects.get(id=mixer['id']).generate_depreciation_schedule()
ok('تم توليد جدول الإهلاك السنوي لكل أصل')

step("ترحيل إهلاك الفترة الأولى للأصلين")


def post_first_year_depreciation(asset_id, asset_label):
    row = call('get', f'/api/fixed-assets/depreciation-schedules/?asset={asset_id}')['results'][0]
    as_accountant()
    call('put', f"/api/fixed-assets/depreciation-schedules/{row['id']}/", {
        'asset': asset_id, 'fiscal_period': period1['id'],
        'depreciation_amount': row['depreciation_amount'],
        'accumulated_depreciation': row['accumulated_depreciation'],
    })
    as_admin()
    call('post', f"/api/fixed-assets/depreciation-schedules/{row['id']}/post/")
    ok(f"إهلاك {asset_label}: {row['depreciation_amount']} مُرحَّل للفترة {period1['name']}")


post_first_year_depreciation(excavator['id'], 'الحفارة')
post_first_year_depreciation(mixer['id'], 'الخلاطة')

# ===========================================================================
# 9) قيد افتتاحي: ضخ رأس المال
# ===========================================================================
step("قيد افتتاحي - ضخ رأس المال")
as_accountant()
je_open = call('post', '/api/journal-entries/entries/', {
    'fiscal_period': period1['id'], 'date': '2026-01-02',
    'description': 'ضخ رأس مال نقدي في بداية النشاط',
    'lines': [
        {'account': acc['1002'], 'debit': '3000000', 'credit': '0', 'description': 'إيداع بنكي - رأس المال'},
        {'account': acc['3001'], 'debit': '0', 'credit': '3000000', 'description': 'رأس المال'},
    ],
})
as_admin()
call('post', f"/api/journal-entries/entries/{je_open['id']}/post/")
ok('تم ترحيل القيد الافتتاحي (3,000,000)')

as_accountant()
je_cashbox = call('post', '/api/journal-entries/entries/', {
    'fiscal_period': period1['id'], 'date': '2026-01-03',
    'description': 'تحويل من البنك لصندوق النثريات',
    'lines': [
        {'account': acc['1001'], 'debit': '300000', 'credit': '0', 'description': 'تغذية الصندوق'},
        {'account': acc['1002'], 'debit': '0', 'credit': '300000', 'description': 'سحب من البنك'},
    ],
})
as_admin()
call('post', f"/api/journal-entries/entries/{je_cashbox['id']}/post/")
ok('تم تمويل صندوق النثريات (300,000)')

# ===========================================================================
# 10) فواتير الشراء (مواد + مقاولو باطن)
# ===========================================================================
step("فواتير الشراء")


def make_invoice(invoice_type, date, party_key, currency_id, items, description=''):
    as_accountant()
    payload = {
        'invoice_type': invoice_type, 'fiscal_period': period_for(date), 'date': date,
        'party': parties[party_key], 'items': items,
    }
    if currency_id:
        payload['currency'] = currency_id
    inv = call('post', '/api/invoicing/invoices/', payload)
    as_admin()
    result = call('post', f"/api/invoicing/invoices/{inv['id']}/post/")
    ok(f"{description or inv['invoice_number']}: مُرحَّلة (قيد {result['journal_entry']})")
    return inv


inv_cement = make_invoice('Purchase', '2026-01-05', 'supplier_local', None, [
    {'product': products['cement'], 'quantity': '500', 'unit_price': '150'},
    {'product': products['sand'], 'quantity': '200', 'unit_price': '300'},
], 'شراء أسمنت ورمل (محلي)')

inv_rebar = make_invoice('Purchase', '2026-01-06', 'supplier_import', usd['id'], [
    {'product': products['rebar'], 'quantity': '20', 'unit_price': '800'},
], 'شراء حديد تسليح مستورد (دولار)')

inv_elec = make_invoice('Purchase', '2026-01-07', 'sub_elec', None, [
    {'product': products['sub_elec_svc'], 'quantity': '1', 'unit_price': '150000'},
], 'أعمال كهربائية - مقاول باطن')

inv_plumb = make_invoice('Purchase', '2026-01-08', 'sub_plumb', None, [
    {'product': products['sub_plumb_svc'], 'quantity': '1', 'unit_price': '90000'},
], 'أعمال سباكة - مقاول باطن')

# ===========================================================================
# 11) فواتير البيع (دفعات إنجاز للعملاء)
# ===========================================================================
step("فواتير البيع - دفعات إنجاز للعملاء")
inv_villa = make_invoice('Sale', '2026-01-15', 'client_villa', None, [
    {'product': products['ms_villa1'], 'quantity': '1', 'unit_price': '800000'},
], 'دفعة إنجاز - مشروع الفيلا')

inv_road = make_invoice('Sale', '2026-01-16', 'client_road', None, [
    {'product': products['ms_road1'], 'quantity': '1', 'unit_price': '1200000'},
], 'دفعة إنجاز - مشروع الطريق')

# ===========================================================================
# 12) قيود يدوية: صرف مواد للمشاريع + مصاريف إدارية
# ===========================================================================
step("قيود يدوية - صرف مواد للمشاريع ومصاريف إدارية")


def manual_je(date, description, lines):
    as_accountant()
    je = call('post', '/api/journal-entries/entries/', {
        'fiscal_period': period_for(date), 'date': date, 'description': description, 'lines': lines,
    })
    as_admin()
    call('post', f"/api/journal-entries/entries/{je['id']}/post/")
    ok(f"{description}: مُرحَّل")
    return je


# المواد المصروفة للمشاريع تُنقل إلى "أعمال تحت التنفيذ" (1006) لا إلى مصروف
# مباشر (5001): تكلفتها الفعلية تُعترف بها في قائمة الدخل فقط عند فوترة دفعة
# الإنجاز المقابلة لها (عبر 5007) — وإلا احتُسبت التكلفة مرتين (مرة كصرف مواد
# مباشر ومرة كتكلفة أعمال منجزة عند البيع). حساب 5001 يبقى متاحًا في الدليل
# لمن يفضّل الاعتراف الفوري بمصروف المواد بدل أسلوب WIP هذا.
manual_je('2026-01-18', 'صرف أسمنت ورمل لمشروع الفيلا (أساسات) - إلى أعمال تحت التنفيذ', [
    {'account': acc['1006'], 'debit': '100000', 'credit': '0', 'cost_center': cc['CC-VILLA'], 'description': 'أعمال تحت التنفيذ - الفيلا'},
    {'account': acc['1005'], 'debit': '0', 'credit': '100000', 'description': 'صرف من المخزون'},
])

manual_je('2026-01-19', 'صرف حديد تسليح لمشروع الطريق - إلى أعمال تحت التنفيذ', [
    {'account': acc['1006'], 'debit': '4800000', 'credit': '0', 'cost_center': cc['CC-ROAD'], 'description': 'أعمال تحت التنفيذ - الطريق'},
    {'account': acc['1005'], 'debit': '0', 'credit': '4800000', 'description': 'صرف من المخزون'},
])

manual_je('2026-01-20', 'إيجار وكهرباء المكتب الرئيسي', [
    {'account': acc['5006'], 'debit': '45000', 'credit': '0', 'cost_center': cc['CC-ADMIN'], 'description': 'مصاريف إدارية عمومية'},
    {'account': acc['1002'], 'debit': '0', 'credit': '45000', 'description': 'دفع من البنك'},
])

# ===========================================================================
# 13) قيد خاطئ ثم عكسه (لتوضيح آلية المراجعة والتصحيح)
# ===========================================================================
step("قيد خاطئ ثم عكسه (create_reversal)")
as_accountant()
je_mistake = call('post', '/api/journal-entries/entries/', {
    'fiscal_period': period1['id'], 'date': '2026-01-21',
    'description': 'قيد إضافي عن أعمال باطن إضافية (يحتوي خطأً متعمدًا للتوضيح)',
    'lines': [
        {'account': acc['5002'], 'debit': '20000', 'credit': '0', 'cost_center': cc['CC-VILLA'], 'description': 'تكلفة إضافية - خطأ'},
        {'account': acc['1002'], 'debit': '0', 'credit': '20000', 'description': 'دفع من البنك'},
    ],
})
as_admin()
call('post', f"/api/journal-entries/entries/{je_mistake['id']}/post/")
ok('تم ترحيل القيد الخاطئ عمدًا')

as_accountant()
reversal = call('post', f"/api/journal-entries/entries/{je_mistake['id']}/reverse/",
                {'date': '2026-01-21'}, expect=(201,))
as_admin()
call('post', f"/api/journal-entries/entries/{reversal['id']}/post/")
ok(f"تم عكس القيد الخاطئ وترحيل قيد العكس ({reversal['entry_number']})")

# ===========================================================================
# 14) سندات القبض والصرف
# ===========================================================================
step("سندات القبض والصرف")


def make_receipt_payment(doc_type, date, party_key, amount, account_code, invoice, alloc_amount, description):
    as_accountant()
    rp = call('post', '/api/payments/receipts-payments/', {
        'document_type': doc_type, 'fiscal_period': period_for(date), 'date': date,
        'party': parties[party_key], 'amount': amount, 'account': acc[account_code],
        'description': description,
    })
    call('post', f"/api/payments/receipts-payments/{rp['id']}/allocate/", {
        'invoice_id': invoice['id'], 'amount': alloc_amount,
    })
    as_admin()
    result = call('post', f"/api/payments/receipts-payments/{rp['id']}/post/")
    ok(f"{description}: مُرحَّل (سند {result['number']})")
    return rp


make_receipt_payment('Payment', '2026-01-22', 'supplier_local', '100000', '1002',
                      inv_cement, '100000', 'دفعة جزئية لمورد الأسمنت والرمل')
make_receipt_payment('Payment', '2026-01-24', 'sub_elec', '150000', '1001',
                      inv_elec, '150000', 'سداد كامل لمقاول الكهرباء')
# ملاحظة مهمة: فاتورة الحديد المستورد (inv_rebar) بعملة أجنبية (USD)، فمبلغها
# total_amount مخزَّن بعملة الفاتورة (16,000 USD) بينما سند الصرف
# ReceiptPayment.amount بلا أي مفهوم عملة (دائمًا بالعملة الأساسية ضمنيًا).
# allocate_to_invoice() تقارن القيمتين مباشرة كأرقام مجرّدة بلا أي تحويل،
# فمحاولة سداد المبلغ المكافئ بالعملة الأساسية (9,600,000) تُرفض لأنه "يتجاوز
# المتبقي على الفاتورة" (16,000)، بينما سداد 16,000 فعليًا سيُرحَّل بالقيد
# كأنه 16,000 بالعملة الأساسية فيُنشئ فرقًا حقيقيًا في دفتر الأستاذ. هذه فجوة
# تصميمية حقيقية (سندات القبض والصرف لم تُوسَّع بعد لتصبح متعددة العملات مثل
# الفواتير) — تُركت هذه الفاتورة بلا سداد عمدًا بدل تمرير مبلغ يُفسِد الأستاذ.
make_receipt_payment('Receipt', '2026-01-26', 'client_villa', '800000', '1002',
                      inv_villa, '800000', 'تحصيل كامل - دفعة الفيلا')
make_receipt_payment('Receipt', '2026-01-27', 'client_road', '700000', '1002',
                      inv_road, '700000', 'تحصيل جزئي - دفعة الطريق')
# ملاحظة: فاتورة مقاول السباكة (inv_plumb) تُركت عمدًا بلا سداد لاستكشافها لاحقًا،
# إلى جانب فاتورة الحديد المستورد (inv_rebar) للسبب الموضّح أعلاه.

# ===========================================================================
# 15) مسيرات الرواتب
# ===========================================================================
step("مسيرات الرواتب - يناير 2026")
PAYSLIPS = [
    ('engineer', '15000', '2000', '500'),
    ('worker', '6000', '0', '0'),
    ('accountant_emp', '10000', '1000', '300'),
]
for key, basic, allowances, deductions in PAYSLIPS:
    as_accountant()
    slip = call('post', '/api/payroll/payslips/', {
        'employee': employees[key], 'fiscal_period': period1['id'],
        'basic_salary': basic, 'allowances': allowances, 'deductions': deductions,
    })
    as_admin()
    result = call('post', f"/api/payroll/payslips/{slip['id']}/post/")
    ok(f"راتب {key}: صافي {slip['net_salary']} - قيد {result['journal_entry']}")

# ===========================================================================
# 16) إقفال الفترة الأولى
# ===========================================================================
step("إقفال فترة يناير 2026")
as_admin()
close_result = call('post', f"/api/journal-entries/close-period/{period1['id']}/")
ok(f"تم إقفال {period1['name']} - قيد الإقفال {close_result['journal_entry']}")

# التحقق من أن الفترة المقفولة فعليًا مرفوضة لأي عملية جديدة
as_accountant()
resp = client.post('/api/journal-entries/entries/', {
    'fiscal_period': period1['id'], 'date': '2026-01-29', 'description': 'محاولة قيد بعد الإقفال',
    'lines': [
        {'account': acc['1001'], 'debit': '100', 'credit': '0'},
        {'account': acc['3001'], 'debit': '0', 'credit': '100'},
    ],
}, format='json')
assert resp.status_code == 400, f"expected rejection, got {resp.status_code}: {resp.data}"
ok('تأكدنا: أي قيد جديد بتاريخ ضمن الفترة المقفولة يُرفض (400) كما هو متوقع')

# ===========================================================================
# 17) فترة فبراير 2026 - تبقى مفتوحة عمدًا لاستكشافها لاحقًا
# ===========================================================================
step("فترة فبراير 2026 (مفتوحة) - استكمال تحصيل دفعة الطريق")
make_receipt_payment('Receipt', '2026-02-05', 'client_road', '500000', '1002',
                      inv_road, '500000', 'تحصيل الدفعة المتبقية - مشروع الطريق')

manual_je_feb = None
as_accountant()
je_feb = call('post', '/api/journal-entries/entries/', {
    'fiscal_period': period2['id'], 'date': '2026-02-10',
    'description': 'مستلزمات مكتبية',
    'lines': [
        {'account': acc['5006'], 'debit': '30000', 'credit': '0', 'cost_center': cc['CC-ADMIN'], 'description': 'مستلزمات مكتبية'},
        {'account': acc['1001'], 'debit': '0', 'credit': '30000', 'description': 'دفع نقدي'},
    ],
})
as_admin()
call('post', f"/api/journal-entries/entries/{je_feb['id']}/post/")
ok('قيد فبراير مُرحَّل، والفترة تبقى مفتوحة عمدًا')

# ===========================================================================
# 18) التحقق من التقارير
# ===========================================================================
step("التحقق من التقارير")
as_admin()
for label, url in [
    ('ميزان المراجعة', '/api/reports/trial-balance/'),
    ('قائمة الدخل', f"/api/reports/income-statement/?fiscal_period={period1['id']}"),
    ('الميزانية العمومية', '/api/reports/balance-sheet/'),
    ('التدفقات النقدية', f"/api/reports/cash-flow/?fiscal_period={period1['id']}"),
    ('كشف حساب طرف (عميل الفيلا)', f"/api/reports/party-statement/{parties['client_villa']}/"),
]:
    call('get', url)
    ok(f"{label}: استجابة سليمة (200)")

# ===========================================================================
# 19) سجل العمليات (Audit Log)
# ===========================================================================
step("سجل العمليات")
logs = call('get', '/api/audit/logs/')
count = logs['count'] if isinstance(logs, dict) and 'count' in logs else len(logs)
ok(f"عدد سجلات العمليات المسجّلة حتى الآن: {count}")

print("\n" + "=" * 70)
print("اكتمل سيناريو شركة الأفق للمقاولات والإنشاءات بنجاح.")
print("=" * 70)
