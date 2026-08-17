from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.common.models import TimeStampedModel

class Product(TimeStampedModel):
    class ValuationMethod(models.TextChoices):
        FIFO = 'FIFO', 'FIFO'
        WEIGHTED_AVERAGE = 'Weighted Average', 'Weighted Average'

    sku = models.CharField(max_length=50, unique=True)
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20, default='piece')
    valuation_method = models.CharField(
        max_length=20,
        choices=ValuationMethod.choices,
        default=ValuationMethod.WEIGHTED_AVERAGE
    )
    average_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    selling_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    inventory_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='products_inventory'
    )
    cogs_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='products_cogs'
    )
    revenue_account = models.ForeignKey(
        'chart_of_accounts.Account',
        on_delete=models.PROTECT,
        related_name='products_revenue',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['sku']

    def __str__(self):
        return f"{self.sku} - {self.name_ar}"

    @property
    def current_stock(self):
        """الرصيد الحالي = مجموع كميات حركات المخزون"""
        total = self.stock_movements.aggregate(total=Sum('quantity'))['total']
        return total or 0

    def clean(self):
        # متوسط التكلفة وسعر البيع لا يمكن أن يكونا سالبين
        if self.average_cost < 0:
            raise ValidationError('Average cost cannot be negative.')
        if self.selling_price < 0:
            raise ValidationError('Selling price cannot be negative.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class StockMovement(TimeStampedModel):
    class MovementType(models.TextChoices):
        PURCHASE = 'Purchase', 'Purchase'
        SALE = 'Sale', 'Sale'
        ADJUSTMENT = 'Adjustment', 'Adjustment'
        TRANSFER = 'Transfer', 'Transfer'
        OPENING = 'Opening', 'Opening'

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField()
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements_created'
    )

    class Meta:
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.product.sku} - {self.movement_type} - {self.quantity}"

    def clean(self):
        # كمية الحركة يجب ألا تكون صفرًا
        if self.quantity == 0:
            raise ValidationError('Quantity cannot be zero.')
        # حركات الإدخال (شراء / رصيد افتتاحي) يجب أن تكون موجبة
        if self.movement_type in [self.MovementType.PURCHASE, self.MovementType.OPENING] and self.quantity < 0:
            raise ValidationError(f'{self.movement_type} movement quantity must be positive.')
        # حركة البيع يجب أن تكون سالبة
        if self.movement_type == self.MovementType.SALE and self.quantity > 0:
            raise ValidationError('Sale movement quantity must be negative.')
        # Adjustment و Transfer: الإشارة حرة عمدًا (قد تُصحِّح بالزيادة أو النقصان)
        # تكلفة الوحدة لا يمكن أن تكون سالبة
        if self.unit_cost < 0:
            raise ValidationError('Unit cost cannot be negative.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # تحديث متوسط التكلفة إذا كانت الطريقة Weighted Average
        if self.product.valuation_method == Product.ValuationMethod.WEIGHTED_AVERAGE:
            self._update_average_cost()

    def _update_average_cost(self):
        """تحديث متوسط التكلفة (Moving Weighted Average) بناءً على الرصيد المتبقي فقط"""
        if self.quantity <= 0:
            return  # حركات الإخراج لا تُغيِّر متوسط تكلفة الوحدة

        product = self.product
        stock_before = product.current_stock - self.quantity
        if stock_before < 0:
            stock_before = 0

        existing_value = stock_before * product.average_cost
        incoming_value = self.quantity * self.unit_cost
        new_quantity = stock_before + self.quantity

        if new_quantity > 0:
            product.average_cost = (existing_value + incoming_value) / new_quantity
            product.save(update_fields=['average_cost', 'updated_at'])
