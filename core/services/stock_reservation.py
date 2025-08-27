from django.db import transaction

from core.models import Product, OrderItem

import logging

logger = logging.getLogger(__name__)


class StockReservationService:
    def __init__(self, product_pk=None, cart_item=None):
        self.product_pk = product_pk
        self.cart_item = cart_item

    def reserve_stock(self):
        try:
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=self.product_pk)
                if product.quantity <= 0:
                    return {'success': False, 'message': f'Unfortunately "{product.name}" is out of stock.'}

                product.quantity -= 1
                product.save()
                return {'success': True, 'message': f'Product "{product.name}" was added to the cart.', 'product': product}

        except Product.DoesNotExist:
            return {'success': False, 'message': 'Unfortunately this product does not exist anymore.'}

    def release_reserved_stock(self):
        if isinstance(self.cart_item, OrderItem):
            return self._process_extracted_data(*self._extract_from_order(self.cart_item))
        elif isinstance(self.cart_item, dict):
            return self._process_extracted_data(*self._extract_from_session(self.cart_item))
        else:
            logger.info(f'Invalid type of cart_item "{self.cart_item}". Skipping stock release.')

    def _process_extracted_data(self, product_pk, product_name, release_quantity):
        try:
            product = Product.objects.get(pk=product_pk)
            product.quantity += release_quantity
            product.save()

            logger.info(f'🔄 Quantity of "{product.name}" was updated | Old value: {product.quantity - release_quantity} | '
                        f'New value: {product.quantity}')
        except Product.DoesNotExist:
            logger.info(f'Product "{product_name}" does not exist anymore (pk=#{product_pk}). Skipping stock release.')
        return {'success': True, 'message': f'Product "{product_name}" was removed from the cart.'}

    def _extract_from_order(self, item):
        return item.product_id_snapshot, item.product_name, item.product_quantity

    def _extract_from_session(self, item):
        return item['product_pk'], item['product_name'], item['quantity']

