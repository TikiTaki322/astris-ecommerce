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
        if self.order is not None:
            self._sync_order_items()
        elif self.session_order is not None:
            self._sync_session_items()
        return self.price_diff

    def _sync_order_items(self):
        for item in self.order.items.all():
            try:
                product = Product.objects.get(pk=item.product_id_snapshot)
            except Product.DoesNotExist:
                logger.info(f'OrderItem "{item.product_name}" does not exist anymore (pk=#{item.product_id_snapshot}).'
                            f'Skipping synchronisation.')
                continue

            current_price = product.price
            order_item_price = item.product_unit_price

            if order_item_price != current_price:
                self.price_diff = True
                if not self.order.price_diff:
                    self.order.price_diff = True
                    self.order.save(update_fields=['price_diff'])

                item.product_unit_price = current_price
                item.product_total_price = Decimal(current_price * item.product_quantity).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
                item.save(update_fields=['product_unit_price', 'product_total_price'])
                logger.info(f'🔄 Synced price for OrderItem: "{item.product_name}" | Method: _sync_order_items() | '
                            f'Old price: {order_item_price} | Current price: {current_price}')

    def _sync_session_items(self):
        for pk, item in self.session_order.items():
            try:
                product = Product.objects.get(pk=pk)
            except Product.DoesNotExist:
                logger.info(f'SessionItem "{item["product_name"]}" does not exist anymore (pk=#{pk}).'
                            f'Skipping synchronisation.')
                continue

            current_price = product.price
            session_item_price = Decimal(item['unit_price'])

            if session_item_price != current_price:
                self.price_diff = True
                item['unit_price'] = str(current_price)
                item['total_price'] = str((current_price * item['quantity']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                logger.info(f'🔄 Synced price for SessionItem: "{product.name}" | Method: _sync_session_items() | '
                            f'Old price: {session_item_price} | Current price: {current_price}')

    def get_amount(self) -> Decimal:
        if self.order:
            self._compute_order_amount()
        elif self.session_order:
            self._compute_session_amount()
        return self.amount

    def _compute_order_amount(self):
        pre_amount = self.order.items.aggregate(total_amount=Sum('product_total_price'))['total_amount'] or Decimal('0.00')
        self.amount = Decimal(pre_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _compute_session_amount(self):
        pre_amount = [Decimal(item['total_price']) for item in self.session_order.values()]
        self.amount = sum(pre_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
