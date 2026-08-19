from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.common.models import TimeStampedModel

class Invoice(TimeStampedModel):
    class InvoiceType(models.TextChoices):
        SALE = 'Sale', 'Sale'
        PURCHASE = 'Purchase', 'Purchase'

    class Status(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        POSTED = 'Posted', 'Posted'
        PARTIALLY_PAID = 'Partially Paid', 'Partially Paid'
        PAID = 'Paid', 'Paid'
        CANCELLED = 'Cancelled', 'Cancelled'

    invoice_type = models.CharField(max_length=20, choices=InvoiceType.choices)
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    fiscal_period = models.ForeignKey(
        'fiscal.FiscalPeriod',
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    party = models.ForeignKey(
        'parties.Party',
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    exchange_rate_used = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='invoices_tax',
        null=True,
        blank=True,
        help_text='مطلوب فقط إذا كانت الفاتورة تحمل مبلغ ضريبة'
    )
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='invoices_discount',
        null=True,
        blank=True,
        help_text='مطلوب فقط إذا كانت الفاتورة تحمل مبلغ خصم'
    )
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    journal_entry = models.ForeignKey(
        'journal_entries.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices_created'
    )

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.party.name_ar}"

    def clean(self):
        if self.date and self.fiscal_period:
            if self.date < self.fiscal_period.start_date or self.date > self.fiscal_period.end_date:
                raise ValidationError('Invoice date must be within fiscal period.')
        if self.total_amount < 0:
            raise ValidationError('Total amount cannot be negative.')

        only_lifecycle_fields_changed = False
        if self.pk:
            old = Invoice.objects.get(pk=self.pk)
            if old.status in [self.Status.POSTED, self.Status.PARTIALLY_PAID, self.Status.PAID]:
                allowed_fields = {'paid_amount', 'status', 'updated_at'}
                changed_fields = []
                for field in self._meta.fields:
                    name = field.name
                    if name in allowed_fields:
                        continue
                    if getattr(old, name) != getattr(self, name):
                        changed_fields.append(name)
                if changed_fields:
                    raise ValidationError(f'الفاتورة المرحّلة لا يمكن تعديلها. الحقول المرفوضة: {", ".join(changed_fields)}')
                only_lifecycle_fields_changed = True

        # فترة مقفولة تمنع إنشاء فاتورة جديدة أو تعديل محتواها، لكنها لا تمنع
        # تحديثات دورة الحياة اللاحقة (تحصيل/سداد عبر allocate_to_invoice) على
        # فاتورة مرحّلة بالفعل تخص فترة أُقفلت بعد ترحيلها — تلك التحديثات
        # محكومة أصلًا بقائمة الحقول المسموحة أعلاه (paid_amount/status).
        if self.fiscal_period and self.fiscal_period.is_closed and not only_lifecycle_fields_changed:
            raise ValidationError('Cannot create invoice in a closed fiscal period.')

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from apps.sequences.services import get_next_number
            from apps.sequences.models import DocumentSequence
            doc_type = (
                DocumentSequence.DocumentType.SALE_INVOICE
                if self.invoice_type == self.InvoiceType.SALE
                else DocumentSequence.DocumentType.PURCHASE_INVOICE
            )
            self.invoice_number = get_next_number(
                doc_type,
                fiscal_year=self.fiscal_period.fiscal_year if self.fiscal_period else None
            )
        # صمّام أمان: عملة أساسية أو عدم تحديد عملة يعني دائمًا سعر صرف = 1،
        # بصرف النظر عمّا أُرسل (الحساب الفعلي لسعر الصرف يتم في الـ serializer).
        if not self.currency_id or self.currency.is_base_currency:
            self.exchange_rate_used = Decimal('1')
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_lines(self):
        return self.items.aggregate(total=Sum('total'))['total'] or 0

    def update_totals(self):
        items_total = self.items.aggregate(total=Sum('total'))['total'] or 0
        self.subtotal = Decimal(items_total).quantize(Decimal('0.01'))
        self.total_amount = Decimal(self.subtotal + self.tax_amount - self.discount).quantize(Decimal('0.01'))
        self.save(update_fields=['subtotal', 'total_amount', 'updated_at'])

    def post(self, user=None):
        if self.status != self.Status.DRAFT:
            raise ValidationError('Only draft invoices can be posted.')
        if not self.items.exists():
            raise ValidationError('Invoice must have at least one item before posting.')
        if self.tax_amount and not self.tax_account:
            raise ValidationError('Tax account is required when tax amount is set.')
        if self.discount and not self.discount_account:
            raise ValidationError('Discount account is required when discount is set.')
        # التحقق من وجود حساب إيراد لكل منتج قبل الترحيل
        for item in self.items.all():
            if self.invoice_type == self.InvoiceType.SALE:
                if not item.product.revenue_account_id:
                    raise ValidationError(
                        f'المنتج {item.product.sku} لا يحتوي على حساب إيراد (revenue_account) — لا يمكن الترحيل.'
                    )
        with transaction.atomic():
            self.update_totals()
            # إنشاء القيد المحاسبي
            from apps.journal_entries.services import create_journal_entry
            journal_entry = create_journal_entry(
                fiscal_period=self.fiscal_period,
                date=self.date,
                description=f"Invoice {self.invoice_number} - {self.party.name_ar}",
                source_type='Invoice',
                source_id=str(self.id),
                created_by=user,
                auto_post=True,
                approved_by=user,
                lines_data=self._get_journal_lines()
            )
            self.journal_entry = journal_entry
            self.status = self.Status.POSTED
            self.save(update_fields=['journal_entry', 'status', 'updated_at'])
            # تسجيل حركات المخزون
            self._post_stock_movements(user)
        return journal_entry

    def _get_journal_lines(self):
        # الطرف (عميل/مورد) يُقيَّد بالمبلغ الفعلي المستحق total_amount
        # (subtotal + tax_amount - discount)، وليس subtotal وحده، حتى يتوازن
        # القيد فعليًا مقابل ما يدين/يُدان به الطرف. الضريبة والخصم على مستوى
        # الفاتورة يُرحَّلان كسطرين منفصلين على حسابيهما المخصصين.
        #
        # القيد المحاسبي دائمًا بالعملة الأساسية (دفتر أستاذ بعملة واحدة).
        # لذلك تُحوَّل كل المبالغ ذات الصلة بعملة الفاتورة (طرف/إيراد/ضريبة/خصم)
        # بضرب سعر الصرف. أما التكلفة (COGS/المخزون) فتبقى كما هي دومًا لأنها
        # مشتقة من average_cost أو من unit_cost المُحوَّل مسبقًا في الـ serializer،
        # وكلاهما بالعملة الأساسية أصلًا.
        rate = self.exchange_rate_used or Decimal('1')

        def conv(amount):
            return Decimal(amount * rate).quantize(Decimal('0.01'))

        lines = []
        if self.invoice_type == self.InvoiceType.SALE:
            lines.append({
                'account': self.party.default_account,
                'debit': conv(self.total_amount),
                'credit': 0,
                'description': f'Sale invoice {self.invoice_number}'
            })
            for item in self.items.all():
                lines.append({
                    'account': item.product.revenue_account,
                    'debit': 0,
                    'credit': conv(item.total),
                    'description': f'Revenue - {item.product.sku}'
                })
                cost = Decimal(item.quantity * item.unit_cost).quantize(Decimal('0.01'))
                lines.append({
                    'account': item.product.cogs_account,
                    'debit': cost,
                    'credit': 0,
                    'description': f'COGS - {item.product.sku}'
                })
                lines.append({
                    'account': item.product.inventory_account,
                    'debit': 0,
                    'credit': cost,
                    'description': f'Inventory out - {item.product.sku}'
                })
            if self.tax_amount:
                lines.append({
                    'account': self.tax_account,
                    'debit': 0,
                    'credit': conv(self.tax_amount),
                    'description': f'Output tax - {self.invoice_number}'
                })
            if self.discount:
                lines.append({
                    'account': self.discount_account,
                    'debit': conv(self.discount),
                    'credit': 0,
                    'description': f'Discount given - {self.invoice_number}'
                })
        else:
            lines.append({
                'account': self.party.default_account,
                'debit': 0,
                'credit': conv(self.total_amount),
                'description': f'Purchase invoice {self.invoice_number}'
            })
            for item in self.items.all():
                lines.append({
                    'account': item.product.inventory_account,
                    'debit': conv(item.total),
                    'credit': 0,
                    'description': f'Inventory in - {item.product.sku}'
                })
            if self.tax_amount:
                lines.append({
                    'account': self.tax_account,
                    'debit': conv(self.tax_amount),
                    'credit': 0,
                    'description': f'Input tax - {self.invoice_number}'
                })
            if self.discount:
                lines.append({
                    'account': self.discount_account,
                    'debit': 0,
                    'credit': conv(self.discount),
                    'description': f'Discount received - {self.invoice_number}'
                })
        return lines

    def _post_stock_movements(self, user):
        from apps.inventory.models import StockMovement
        for item in self.items.all():
            if self.invoice_type == self.InvoiceType.SALE:
                quantity = -item.quantity  # سالب للإخراج
                movement_type = StockMovement.MovementType.SALE
            else:
                quantity = item.quantity  # موجب للإدخال
                movement_type = StockMovement.MovementType.PURCHASE
            StockMovement.objects.create(
                product=item.product,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=item.unit_cost,
                reference_type='Invoice',
                reference_id=str(self.id),
                date=self.date,
                created_by=user
            )

class InvoiceItem(TimeStampedModel):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        related_name='invoice_items'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'

    def __str__(self):
        return f"{self.product.sku} - {self.quantity} x {self.unit_price}"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError('Quantity must be positive.')
        if self.unit_price < 0 or self.unit_cost < 0:
            raise ValidationError('Prices cannot be negative.')

    def save(self, *args, **kwargs):
        self.total = Decimal((self.quantity * self.unit_price) - self.discount).quantize(Decimal('0.01'))
        self.full_clean()
        super().save(*args, **kwargs)
