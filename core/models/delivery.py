from decimal import Decimal

from django.db import models


class DeliverySettings(models.Model):
    delivery_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'))
    delivery_price = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('8.50'))

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]