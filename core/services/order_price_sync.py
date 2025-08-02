from django.shortcuts import get_object_or_404
from django.db.models import Sum
from core.models import Product

from decimal import Decimal, ROUND_HALF_UP

import logging

logger = logging.getLogger(__name__)


class OrderPriceSyncService:
    def __init__(self, order=None, session_order=None):
        self.order = order
        self.session_order = session_order
        self.price_diff = False
        self.amount = Decimal('0.00')

    def sync(self) -> bool:
        if self.order:
            self._sync_order_items()
        elif self.session_order:
            self._sync_session_items()
        return self.price_diff

    def _sync_order_items(self):
        for item in self.order.items.select_related('product'):
            product = item.product
            current_price = product.price
            order_item_price = item.unit_price

            if order_item_price != current_price:
                self.price_diff = True
                item.unit_price = current_price
                item.price = Decimal(current_price * item.quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                item.save(update_fields=['unit_price', 'price'])
                logger.info(f'🔄 Synced price for OrderItem: "{product.name}" | Method: _sync_order_items() | '
                            f'Old price: {order_item_price} | Current price: {current_price}')

    def _sync_session_items(self):
        for pk, item in self.session_order.items():
            product = get_object_or_404(Product, pk=pk)
            current_price = product.price
            cart_item_price = Decimal(item['unit_price'])

            if cart_item_price != current_price:
                self.price_diff = True
                item['unit_price'] = str(current_price)
                item['price'] = str((current_price * item['quantity']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                logger.info(f'🔄 Synced price for SessionItem: "{product.name}" | Method: _sync_session_items() | '
                            f'Old price: {cart_item_price} | Current price: {current_price}')

    def get_amount(self) -> Decimal:
        if self.order:
            self._compute_order_amount()
        elif self.session_order:
            self._compute_session_amount()
        return self.amount

    def _compute_order_amount(self):
        pre_amount = self.order.items.aggregate(total_amount=Sum('price'))['total_amount'] or Decimal('0.00')
        self.amount = Decimal(pre_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _compute_session_amount(self):
        pre_amount = [Decimal(item['price']) for item in self.session_order.values()]
        self.amount = sum(pre_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
