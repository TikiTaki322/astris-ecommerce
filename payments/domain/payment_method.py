from django.db import models


class PaymentMethod(models.TextChoices):
    TWINT = 'twint', 'Twint'
    CARD = 'card', 'Card'
    PAYPAL = 'paypal', 'Paypal'
    CRYPTO = 'crypto', 'Crypto'