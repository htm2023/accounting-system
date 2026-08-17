from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import TimeStampedModel

class DocumentSequence(TimeStampedModel):
    class DocumentType(models.TextChoices):
        JOURNAL_ENTRY = 'JournalEntry', 'Journal Entry'
        SALE_INVOICE = 'SaleInvoice', 'Sale Invoice'
        PURCHASE_INVOICE = 'PurchaseInvoice', 'Purchase Invoice'
        RECEIPT = 'Receipt', 'Receipt'
        PAYMENT = 'Payment', 'Payment'

    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
    )
    prefix = models.CharField(max_length=10, blank=True, default='')
    current_number = models.PositiveIntegerField(default=0)
    fiscal_year = models.ForeignKey(
        'fiscal.FiscalYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_sequences'
    )

    class Meta:
        verbose_name = 'Document Sequence'
        verbose_name_plural = 'Document Sequences'
        unique_together = ('document_type', 'fiscal_year')

    def __str__(self):
        return f"{self.document_type} - {self.prefix}{self.current_number}"

    def clean(self):
        if self.fiscal_year:
            qs = DocumentSequence.objects.filter(
                document_type=self.document_type,
                fiscal_year=self.fiscal_year
            ).exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError('A sequence for this document type and fiscal year already exists.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
