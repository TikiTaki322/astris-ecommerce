import logging
from decimal import Decimal, ROUND_HALF_UP

from core.models import Product, OrderItem

logger = logging.getLogger(__name__)


class OrderItemPriceSyncService:
    def __init__(self, order):
        self.order = order
        self.price_diff = False

    def sync(self) -> bool:
        items = list(self.order.items.all())

        product_pks = [item.product_pk_snapshot for item in items]
        products = {p.pk: p for p in Product.objects.filter(pk__in=product_pks)}
        synced_items = []

        for item in items:
            if product := products.get(item.product_pk_snapshot, None):
                current_price = product.price
                order_item_price = item.product_unit_price

                if order_item_price != current_price:
                    item.product_unit_price = current_price
                    item.product_total_price = Decimal(current_price * item.product_quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    synced_items.append(item)

                    logger.info(
                        f'Synced OrderItem: "{item.product_name}" | '
                        f'Old price: {order_item_price} -> New price: {current_price}'
                    )
            else:
                logger.warning(
                    f'OrderItem "{item.product_name}" (pk={item.product_pk_snapshot}) does not exist anymore. '
                    f'Skipping synchronisation'
                )
                continue

        if synced_items:
            OrderItem.objects.bulk_update(synced_items, ['product_unit_price', 'product_total_price'])
            self.price_diff = True

        return self.price_diff