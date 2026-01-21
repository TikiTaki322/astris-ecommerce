from decimal import Decimal

from django.db import models

from accounts.models import CustomerProfile
from core.domain import OrderStatus
from shared.models import TimeStampedModel


class Order(TimeStampedModel):

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status=OrderStatus.PENDING),
                name='unique_pending_order_per_user'
            )
        ]

    user = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='orders')
    tracking_info = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    items_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    delivery_amount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    paid_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    notified_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    expired_at = models.DateTimeField(blank=True, null=True)

    shipping_email = models.EmailField(max_length=40, blank=True, null=True)
    shipping_first_name = models.CharField(max_length=56)
    shipping_last_name = models.CharField(max_length=56)
    shipping_phone = models.CharField(max_length=24)
    shipping_country = models.CharField(max_length=56)
    shipping_city = models.CharField(max_length=56)
    shipping_postal_code = models.CharField(max_length=16)
    shipping_street = models.CharField(max_length=56)
    shipping_house_number = models.CharField(max_length=16)
    shipping_apartment = models.CharField(max_length=16, blank=True, null=True)
    shipping_additional_info = models.CharField(max_length=128, blank=True, null=True)

    def latest_payment(self):
        if 'payments' in getattr(self, '_prefetched_objects_cache', {}):
            return next((payment for payment in self._prefetched_objects_cache['payments']), None)
        return self.payments.order_by('-created_at').first()

    def __str__(self):
        return f'Order #{self.pk}'