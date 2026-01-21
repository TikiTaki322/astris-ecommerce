import logging

from django.db import transaction
from django.db.models import F

from core.models import Product, OrderItem

logger = logging.getLogger(__name__)


class StockReservationService:
    def __init__(self, product_pk=None, cart_item=None):
        self.product_pk = product_pk
        self.cart_item = cart_item

    def reserve_stock(self):
        try:
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=self.product_pk)
                if product.quantity > 0:
                    product.quantity -= 1
                    product.save(update_fields=['quantity'])
                    return {'success': True, 'message': f'Product "{product.name}" was added to the cart',
                            'product': product}
                return {'success': False, 'message': f'Unfortunately "{product.name}" is out of stock'}

        except Product.DoesNotExist:
            return {'success': False, 'message': 'Unfortunately this product does not exist anymore'}

    def release_reserved_stock(self):
        if isinstance(self.cart_item, OrderItem):
            return self._process_extracted_data(*self._extract_from_order(self.cart_item))
        elif isinstance(self.cart_item, dict):
            return self._process_extracted_data(*self._extract_from_session(self.cart_item))
        else:
            logger.warning(f'Invalid type of cart_item "{self.cart_item}". Skipping stock release')

    def _process_extracted_data(self, product_pk, product_name, release_quantity):
        updated = Product.objects.filter(pk=product_pk).update(
            quantity=F('quantity') + release_quantity
        )
        if updated:
            logger.info(f'Quantity of "{product_name}" was updated | Released: +{release_quantity}')
            return {'success': True, 'message': f'Product "{product_name}" was removed from the cart'}

        logger.warning(f'Product "{product_name}" (pk={product_pk}) does not exist anymore. Skipping stock release')
        return {'success': False, 'message': f'Product "{product_name}" does not exist anymore'}

    def _extract_from_order(self, item):
        return item.product_pk_snapshot, item.product_name, item.product_quantity

    def _extract_from_session(self, item):
        return item['product_pk'], item['product_name'], item['quantity']
