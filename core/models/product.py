from decimal import Decimal

from django.db import models

from shared.models import TimeStampedModel
from .category import Category


class Product(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=56, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    quantity = models.PositiveIntegerField(default=1)
    description = models.CharField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    primary_image_url = models.URLField(blank=True)

    def get_primary_image(self):
        if 'images' in getattr(self, '_prefetched_objects_cache', {}):
            return next((img for img in self._prefetched_objects_cache['images'] if img.is_primary), None)
        return self.images.filter(is_primary=True).first()

    def get_secondary_image(self):
        if 'images' in getattr(self, '_prefetched_objects_cache', {}):
            return next((img for img in self._prefetched_objects_cache['images'] if not img.is_primary), None)
        return self.images.filter(is_primary=False).first()

    def __str__(self):
        return f'{self.name}'


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=1)
    alt_text = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ['position']

    def save(self, *args, **kwargs):
        """
        Invariant:
        - save() only guarantees:
            - exactly one primary image
            - new images without explicit position go to the end
        - canonical ordering and alt_text normalization
          MUST be enforced by ProductImageSyncService
        """

        images_qs = self.product.images.exclude(pk=self.pk)
        has_primary = images_qs.filter(is_primary=True).exists()

        if not has_primary:
            self.is_primary = True

        if self.is_primary:
            images_qs.update(is_primary=False)

        if not self.is_primary and self.position == 1:
            self.position = images_qs.count() + 1

        super().save(*args, **kwargs)

        if self.is_primary:
            self.product.primary_image_url = self.image.url
            self.product.save(update_fields=['primary_image_url'])