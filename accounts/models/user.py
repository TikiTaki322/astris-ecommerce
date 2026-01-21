from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from accounts.domain import UserRole
from accounts.utils import generate_verification_token
from shared.models import TimeStampedModel
from .manager import UserManager


class UserProfile(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(max_length=40, unique=True)
    role = models.CharField(max_length=16, choices=UserRole.choices, default=UserRole.CUSTOMER)

    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def refresh_verification_token(self):
        token = generate_verification_token()
        self.verification_token = token
        self.email_sent_at = timezone.now()
        self.save(update_fields=['verification_token', 'email_sent_at'])
        return token

    def eliminate_verification_token(self):
        self.verification_token = None
        self.email_sent_at = None
        self.save(update_fields=['verification_token', 'email_sent_at'])

    def __str__(self):
        return f'{self.email}'


class CustomerProfile(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='customer_profile')

    def __str__(self):
        return f'{self.user.email}'