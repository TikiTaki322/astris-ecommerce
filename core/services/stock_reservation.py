from django.shortcuts import get_object_or_404
from core.models import Product, OrderItem

import logging

logger = logging.getLogger(__name__)


# class StockReservationService:

reserve_stock
release_reserved_stock
def release_product_resources(obj):
    if isinstance(obj, OrderItem):
        product_id = obj.product_id_snapshot
        return_value = obj.product_quantity

    elif isinstance(obj, dict):
        # If session_order obj
        product_id = obj['product_pk']
        return_value = obj['quantity']

    try:
        product = Product.objects.get(pk=product_id)
        product.quantity += return_value
        product.save()
        logger.info(f'🔄 Quantity of "{product.name}" was updated | '
                    f'Old value: {product.quantity - return_value} | New value: {product.quantity}')
    except Product.DoesNotExist:
        logger.info(f'Product pk#{product_id} does not exist. Skipping stock release.')