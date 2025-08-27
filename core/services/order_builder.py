from django.contrib.auth import get_user_model

from core.models import Product, Order, OrderItem
from .order_price_sync import OrderPriceSyncService
from .stock_reservation import StockReservationService

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class OrderBuilderService:
    def __init__(self, session_order: Optional[dict] = None, user: Optional[User] = None):
        self.session_order = session_order or {}
        self.user = user

    def build(self):
        if not self.session_order:
            return None

        elif self.user.is_staff or self.user.role == 'seller':
            for item in self.session_order.values():
                StockReservationService(cart_item=item).release_reserved_stock()
                logger.info(f'SessionItem "{item["product_name"]}" was released for a privileged user: {self.user}')
            return None

        order, created = Order.objects.get_or_create(user=self.user.customer_profile, status=Order.OrderStatus.PENDING)

        bd_price_diff = OrderPriceSyncService(order=order).sync() if not created else False
        session_service = OrderPriceSyncService(session_order=self.session_order)
        session_price_diff = session_service.sync()

        if is_inconsistency := bool(bd_price_diff or session_price_diff):
            order.price_diff = is_inconsistency
            order.save(update_fields=['price_diff'])
        logger.info(f"🚀 {self.__class__.__name__} was triggered | price_diff: {order.price_diff}")

        self._update_order_items(session_service.session_order, order)
        return order

    def _update_order_items(self, session_order_collection, order):
        for pk, item in session_order_collection.items():
            self._create_or_update_item(pk, item, order)
        print('--'*40)

    def _create_or_update_item(self, pk, item, order):
        try:
            product = Product.objects.get(pk=pk)
            order_item, created = OrderItem.objects.get_or_create(order=order, product_id_snapshot=product.pk)
            order_item.product_id_snapshot = product.pk
            order_item.product_name = product.name
            order_item.product_description = product.description
            order_item.product_quantity = order_item.product_quantity + item['quantity'] if not created else item['quantity']
            order_item.product_unit_price = product.price
            order_item.product_total_price = Decimal(product.price * order_item.product_quantity).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)
            order_item.save()

            logger.info(
                f'🔄Updated OrderItem: "{order_item.product_name}" |'
                f'Old quantity: {order_item.product_quantity - item["quantity"]} | '
                f'Current quantity: {order_item.product_quantity}' if not created else
                f'✅ Created OrderItem: "{order_item.product_name}"')
        except Product.DoesNotExist:
            logger.info(f'Product "{item["product_name"]}" does not exist anymore (pk=#{pk}).'
                        f'Skipping order_item building for this session_item.')


