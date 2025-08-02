from django.shortcuts import get_object_or_404
from core.models import Product, OrderItem

import logging

logger = logging.getLogger(__name__)


def release_product_resources(obj):
    if isinstance(obj, OrderItem):
        product = get_object_or_404(Product, pk=obj.product.pk)
        return_value = obj.quantity

    elif isinstance(obj, dict):
        # If session_order obj
        product = get_object_or_404(Product, pk=obj['product_pk'])
        return_value = obj['quantity']

    product.quantity += return_value
    product.save()
    logger.info(f'🔄 Quantity of "{product.name}" was updated | '
                f'Old value: {product.quantity - return_value} | New value: {product.quantity}')
