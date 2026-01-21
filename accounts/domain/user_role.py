from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    SELLER = 'seller', 'Seller'
    MANAGER = 'manager', 'Manager'
    CUSTOMER = 'customer', 'Customer'