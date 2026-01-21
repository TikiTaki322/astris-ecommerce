from django.db import models

from core.models import Order
from payments.domain import PaymentMethod, PaymentStatus
from shared.models import TimeStampedModel


class Payment(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    transaction = models.CharField(max_length=128, blank=True, null=True)  # Outer payment provider
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Payment #{self.pk} by {self.order.user}'
