from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from shared.models import TimeStampedModel, SoftDeleteModel
from .utils import generate_email_verification_token


class UserProfile(AbstractUser, TimeStampedModel, SoftDeleteModel):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        SELLER = 'seller', 'Seller'
        ADMIN = 'admin', 'Admin'

    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    email = models.EmailField(max_length=50, unique=True)
    username = models.CharField(max_length=30, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def refresh_verification_token(self):
        self.email_verification_token = generate_email_verification_token()
        self.email_sent_at = timezone.now()
        self.save()

    def __str__(self):
        return f'{self.username}'


class CustomerProfile(TimeStampedModel, SoftDeleteModel):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='customer_profile')

    def __str__(self):
        return f'{self.user.username}'


class SellerProfile(TimeStampedModel, SoftDeleteModel):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='seller_profile')

    def __str__(self):
        return f'{self.user.username}'


class ShippingInfo(TimeStampedModel):
    user = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='shipping_info')
    email = models.EmailField(max_length=50, blank=True, null=True)

    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=64)
    city = models.CharField(max_length=64)
    postal_code = models.CharField(max_length=10)
    street = models.CharField(max_length=128)
    house_number = models.CharField(max_length=10)
    apartment = models.CharField(max_length=10, blank=True, null=True)
    additional_info = models.CharField(max_length=256, blank=True, null=True)


class UserLoginHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='login_history')
    email = models.EmailField(max_length=50, blank=True, null=True)

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
