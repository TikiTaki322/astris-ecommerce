from django.db import models

from shared.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(max_length=56, unique=True)
    description = models.CharField(max_length=256, blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f'{self.name}'