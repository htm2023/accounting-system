from decimal import Decimal
from .models import ExchangeRateHistory


def get_exchange_rate(currency, date):
    """يُعيد سعر الصرف الواجب استخدامه لعملة معيّنة في تاريخ معيّن.

    - يُعيد Decimal('1') للعملة الأساسية أو عند عدم تحديد عملة.
    - لغير ذلك، يبحث عن آخر سعر مسجّل بتاريخ أقل من أو يساوي التاريخ المطلوب.
    - يُعيد None إذا لم يوجد أي سعر صرف مسجّل لهذه العملة حتى ذلك التاريخ.
    """
    if currency is None or currency.is_base_currency:
        return Decimal('1')
    latest = (
        ExchangeRateHistory.objects
        .filter(currency=currency, date__lte=date)
        .order_by('-date')
        .first()
    )
    return latest.rate if latest else None
