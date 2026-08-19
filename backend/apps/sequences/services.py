from django.db import transaction
from django.db.models import F
from .models import DocumentSequence

# بادئات افتراضية عند إنشاء تسلسل جديد لأول مرة. ضرورية لأن بعض الحقول التي
# تستهلك هذا الرقم (Invoice.invoice_number، ReceiptPayment.number) فريدة
# عالميًا بينما تسلسلاتها هنا مستقلة لكل نوع مستند — فبدون بادئة مميزة
# يتصادم أول رقم لفاتورة بيع مع أول رقم لفاتورة شراء (كلاهما "1")، وكذلك
# أول سند قبض مع أول سند صرف.
DEFAULT_PREFIXES = {
    DocumentSequence.DocumentType.SALE_INVOICE: 'SI-',
    DocumentSequence.DocumentType.PURCHASE_INVOICE: 'PI-',
    DocumentSequence.DocumentType.RECEIPT: 'RC-',
    DocumentSequence.DocumentType.PAYMENT: 'PV-',
    DocumentSequence.DocumentType.JOURNAL_ENTRY: 'JE-',
}

def get_next_number(document_type, fiscal_year=None):
    """
    تُرجع الرقم التسلسلي التالي لنوع مستند معين.
    إذا تم تمرير fiscal_year، سيتم استخدام تسلسل خاص بتلك السنة المالية.
    الدالة آمنة ضد التزامن باستخدام select_for_update().
    """
    with transaction.atomic():
        filter_kwargs = {'document_type': document_type}
        if fiscal_year:
            filter_kwargs['fiscal_year'] = fiscal_year
        else:
            filter_kwargs['fiscal_year__isnull'] = True

        seq = DocumentSequence.objects.select_for_update().filter(**filter_kwargs).first()
        if not seq:
            seq = DocumentSequence.objects.create(
                document_type=document_type,
                fiscal_year=fiscal_year,
                prefix=DEFAULT_PREFIXES.get(document_type, ''),
                current_number=0
            )

        DocumentSequence.objects.filter(pk=seq.pk).update(current_number=F('current_number') + 1)
        seq.refresh_from_db()
        return f"{seq.prefix}{seq.current_number}"
