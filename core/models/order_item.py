from decimal import Decimal

from django.db import models

from shared.models import TimeStampedModel
from .order import Order


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_pk_snapshot = models.PositiveIntegerField()
    product_image_url = models.URLField(blank=True)
    product_name = models.CharField(max_length=56)
    product_quantity = models.PositiveIntegerField(default=1)
    product_description = models.CharField(max_length=256, blank=True)
    product_unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    product_total_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f'{self.product_name}'