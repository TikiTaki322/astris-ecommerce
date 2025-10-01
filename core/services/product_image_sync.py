from core.models import Product, ProductImage

import logging

logger = logging.getLogger(__name__)


class ProductImageSyncService:
    def __init__(self, product):
        self.product = product
        self.images = list(self.product.images.order_by('-is_primary', 'position', '-updated_at', 'pk'))

    def sync_product_images(self):
        synced_images = []
        for idx, image in enumerate(self.images, 1):
            needs_update = False

            if image.position != idx:
                image.position = idx
                needs_update = True

            new_alt_text = self._generate_alt_text(idx)
            if image.alt_text != new_alt_text:
                image.alt_text = new_alt_text
                needs_update = True

            if needs_update:
                synced_images.append(image)

        if synced_images:
            ProductImage.objects.bulk_update(synced_images, ['position', 'alt_text'])
            logger.info(f'🔄 Synced image`s position for "{self.product.name}": {[img.alt_text[:7] for img in synced_images]}')

    def _generate_alt_text(self, index):
        category = self.product.category.name if self.product.category else 'General'
        return f"img. #{index}, {self.product.name} - {category}"