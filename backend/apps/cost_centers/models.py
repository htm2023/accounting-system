from django.db import models
from apps.common.models import TimeStampedModel

class CostCenter(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cost Center'
        verbose_name_plural = 'Cost Centers'

    def __str__(self):
        return f"{self.code} - {self.name_ar}"
