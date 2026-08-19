from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.common.models import TimeStampedModel


def _normalized_currency_id(currency):
    """يُطبِّع العملة الأساسية (أو عدم تحديد عملة) دائمًا إلى None، حتى تُقارَن
    فاتورة بلا عملة محددة مع فاتورة بعملة أساسية صريحة على أنهما متكافئتان."""
    if currency is None or currency.is_base_currency:
        return None
    return currency.id


class ReceiptPayment(TimeStampedModel):
    class DocumentType(models.TextChoices):
        RECEIPT = 'Receipt', 'Receipt'
        PAYMENT = 'Payment', 'Payment'

    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    number = models.CharField(max_length=50, unique=True, editable=False)
    fiscal_period = models.ForeignKey(
        'fiscal.FiscalPeriod',
        on_delete=models.PROTECT,
        related_name='receipts_payments'
    )
    date = models.DateField()
    party = models.ForeignKey(
        'parties.Party',
        on_delete=models.PROTECT,
        related_name='receipts_payments'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='receipts_payments'
    )
    currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipts_payments'
    )
    exchange_rate_used = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    description = models.TextField(blank=True, null=True)
    journal_entry = models.ForeignKey(
        'journal_entries.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipts_payments'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipts_payments_created'
    )

    class Meta:
        verbose_name = 'Receipt/Payment'
        verbose_name_plural = 'Receipts/Payments'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.number} - {self.document_type} - {self.amount}"

    def clean(self):
        if self.fiscal_period and self.fiscal_period.is_closed:
            raise ValidationError('Cannot create document in a closed fiscal period.')
        if self.date and self.fiscal_period:
            if self.date < self.fiscal_period.start_date or self.date > self.fiscal_period.end_date:
                raise ValidationError('Document date must be within fiscal period.')
        if self.amount <= 0:
            raise ValidationError('Amount must be positive.')
        if self.pk:
            old = ReceiptPayment.objects.get(pk=self.pk)
            if old.journal_entry_id is not None:
                allowed_fields = {'journal_entry', 'updated_at'}
                changed_fields = []
                for field in self._meta.fields:
                    name = field.name
                    if name in allowed_fields:
                        continue
                    if getattr(old, name) != getattr(self, name):
                        changed_fields.append(name)
                if changed_fields:
                    raise ValidationError(f'السند المرحّل لا يمكن تعديله. الحقول المرفوضة: {", ".join(changed_fields)}')

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.sequences.services import get_next_number
            from apps.sequences.models import DocumentSequence
            doc_type = (
                DocumentSequence.DocumentType.RECEIPT
                if self.document_type == self.DocumentType.RECEIPT
                else DocumentSequence.DocumentType.PAYMENT
            )
            self.number = get_next_number(
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
    def total_allocated(self):
        return self.payment_allocations.aggregate(total=Sum('allocated_amount'))['total'] or 0

    @property
    def unallocated_amount(self):
        return self.amount - self.total_allocated

    def allocate_to_invoice(self, invoice, amount):
        if invoice.party_id != self.party_id:
            raise ValidationError('Invoice party does not match the receipt/payment party.')
        # amount هنا بعملة السند نفسها، وتُقارَن مباشرة (بلا تحويل) بمبلغ
        # الفاتورة الذي هو أيضًا بعملة الفاتورة نفسها — فيجب أن تتطابق
        # العملتان (أو تكونا كلتاهما العملة الأساسية) حتى تُقارَن كأرقام
        # بنفس الوحدة فعليًا. سداد فاتورة بعملة مختلفة عن عملة السند غير
        # مدعوم (يتطلب محاسبة فروق أسعار صرف منفصلة، خارج نطاق هذا النظام).
        if _normalized_currency_id(self.currency) != _normalized_currency_id(invoice.currency):
            raise ValidationError('عملة السند يجب أن تطابق عملة الفاتورة المخصَّص لها.')
        if self.unallocated_amount < amount:
            raise ValidationError('Allocation amount exceeds unallocated amount.')
        if invoice.status == 'Paid':
            raise ValidationError('Invoice is already fully paid.')
        if amount <= 0:
            raise ValidationError('Allocation amount must be positive.')
        # لا يمكن تخصيص دفعة لفاتورة غير مرحّلة
        if invoice.status not in ['Posted', 'Partially Paid']:
            raise ValidationError('لا يمكن تخصيص دفعة لفاتورة غير مرحّلة (Draft).')
        # التحقق من أن المبلغ لا يتجاوز المتبقي على الفاتورة
        remaining_invoice = invoice.total_amount - invoice.paid_amount
        if amount > remaining_invoice:
            raise ValidationError('Allocation amount exceeds remaining invoice amount.')
        with transaction.atomic():
            from .models import PaymentAllocation
            PaymentAllocation.objects.create(
                receipt_payment=self,
                invoice=invoice,
                allocated_amount=amount
            )
            invoice.paid_amount += amount
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = 'Paid'
            elif invoice.paid_amount > 0:
                invoice.status = 'Partially Paid'
            invoice.save(update_fields=['paid_amount', 'status', 'updated_at'])

    def post(self, user=None):
        if self.journal_entry:
            raise ValidationError('Document is already posted.')
        if self.unallocated_amount > 0:
            raise ValidationError('Cannot post with unallocated amount. Allocate full amount first.')
        # إنشاء القيد المحاسبي
        from apps.journal_entries.services import create_journal_entry
        # القيد دائمًا بالعملة الأساسية؛ amount بعملة السند نفسها فتُحوَّل
        # بضرب سعر الصرف (rate=1 دائمًا للعملة الأساسية أو عند عدم تحديدها).
        rate = self.exchange_rate_used or Decimal('1')
        converted_amount = Decimal(self.amount * rate).quantize(Decimal('0.01'))
        lines = []
        if self.document_type == self.DocumentType.RECEIPT:
            # مدين: حساب البنك/الخزينة، دائن: حساب العميل
            # ملاحظة: allocate_to_invoice() يفرض أن كل التخصيصات لنفس طرف السند
            # (self.party)، لذا حساب الطرف واحد دائمًا بغض النظر عن عدد الفواتير.
            lines.append({
                'account': self.account,
                'debit': converted_amount,
                'credit': 0,
                'description': f'Receipt {self.number} from {self.party.name_ar}'
            })
            lines.append({
                'account': self.party.default_account,
                'debit': 0,
                'credit': converted_amount,
                'description': f'Receipt {self.number} allocation'
            })
        else:  # Payment
            # مدين: حساب المورد، دائن: حساب البنك/الخزينة
            lines.append({
                'account': self.party.default_account,
                'debit': converted_amount,
                'credit': 0,
                'description': f'Payment {self.number} to {self.party.name_ar}'
            })
            lines.append({
                'account': self.account,
                'debit': 0,
                'credit': converted_amount,
                'description': f'Payment {self.number}'
            })
        with transaction.atomic():
            journal_entry = create_journal_entry(
                fiscal_period=self.fiscal_period,
                date=self.date,
                description=f"{self.document_type} {self.number} - {self.party.name_ar}",
                source_type='Payment',
                source_id=str(self.id),
                created_by=user,
                auto_post=True,
                approved_by=user,
                lines_data=lines
            )
            self.journal_entry = journal_entry
            self.save(update_fields=['journal_entry', 'updated_at'])
        return journal_entry

class PaymentAllocation(TimeStampedModel):
    receipt_payment = models.ForeignKey(
        ReceiptPayment,
        on_delete=models.CASCADE,
        related_name='payment_allocations'
    )
    invoice = models.ForeignKey(
        'invoicing.Invoice',
        on_delete=models.PROTECT,
        related_name='payment_allocations'
    )
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        verbose_name = 'Payment Allocation'
        verbose_name_plural = 'Payment Allocations'

    def __str__(self):
        return f"{self.receipt_payment.number} -> {self.invoice.invoice_number}: {self.allocated_amount}"

    def clean(self):
        if self.allocated_amount <= 0:
            raise ValidationError('Allocated amount must be positive.')
