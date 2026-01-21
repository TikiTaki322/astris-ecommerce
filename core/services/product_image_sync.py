import logging

from core.models import ProductImage

logger = logging.getLogger(__name__)


class ProductImageSyncService:
    """
    Canonizes product images state:
    - primary image always first
    - positions normalized starting from 1
    - alt_text regenerated based on final order
    """
    def __init__(self, product):
        self.product = product
        self.images = list(self.product.images.order_by('-is_primary', 'position', '-updated_at', 'pk'))

    def sync_product_images(self):
        synced_images = []
        for idx, image in enumerate(self.images, 1):
            new_alt_text = self._generate_alt_text(idx)

            if image.position != idx or image.alt_text != new_alt_text:
                image.position = idx
                image.alt_text = new_alt_text
                synced_images.append(image)

        if synced_images:
            ProductImage.objects.bulk_update(synced_images, ['position', 'alt_text'])
            logger.info(f'Images synchronized for "{self.product.name}"')

    def _generate_alt_text(self, idx):
        category = self.product.category.name if self.product.category else 'General'
        return f"img. #{idx}, {self.product.name} - {category}"