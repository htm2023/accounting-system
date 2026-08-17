from django.db import transaction
from django.db.models import F
from .models import DocumentSequence

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
                prefix='',
                current_number=0
            )

        DocumentSequence.objects.filter(pk=seq.pk).update(current_number=F('current_number') + 1)
        seq.refresh_from_db()
        return f"{seq.prefix}{seq.current_number}"
