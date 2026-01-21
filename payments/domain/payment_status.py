from django.db import models


class PaymentStatus(models.TextChoices):
    INITIATED = 'initiated', 'Initiated'
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'