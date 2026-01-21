from django.db import models

from shared.models import TimeStampedModel
from .user import CustomerProfile


class ShippingInfo(TimeStampedModel):
    user = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='shipping_info')
    email = models.EmailField(max_length=40, blank=True, null=True)

    first_name = models.CharField(max_length=56)
    last_name = models.CharField(max_length=56)
    phone = models.CharField(max_length=24)
    country = models.CharField(max_length=56)
    city = models.CharField(max_length=56)
    postal_code = models.CharField(max_length=16)
    street = models.CharField(max_length=56)
    house_number = models.CharField(max_length=16)
    apartment = models.CharField(max_length=16, blank=True, null=True)
    additional_info = models.CharField(max_length=128, blank=True, null=True)