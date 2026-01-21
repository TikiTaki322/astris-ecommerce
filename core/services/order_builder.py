import logging
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model

from core.domain import OrderStatus
from core.models import Product, Order, OrderItem
from shared.permissions.utils import backoffice_member_check
from .order_amount_calc import OrderOrchestrationService
from .stock_reservation import StockReservationService

logger = logging.getLogger(__name__)
User = get_user_model()


class OrderBuilderService:
    def __init__(self, session_order: dict, user: User):
        self.session_items = session_order.get('items', None) if session_order else None
        self.user = user

    def build(self):

        if backoffice_member_check(self.user):
            self._handle_backoffice_member_session()
            return None

        order, _ = Order.objects.get_or_create(user=self.user.customer_profile, status=OrderStatus.PENDING)
        items = list(self.session_items.values())
        built_items = []

        product_pks = [item['product_pk'] for item in items]
        products = {p.pk: p for p in Product.objects.filter(pk__in=product_pks)}

        for item in items:
            if product := products.get(item['product_pk'], None):
                order_item, created = OrderItem.objects.get_or_create(order=order, product_pk_snapshot=product.pk)
                order_item.product_pk_snapshot = product.pk
                order_item.product_image_url = item['product_image_url']
                order_item.product_name = product.name
                order_item.product_description = product.description
                order_item.product_quantity = order_item.product_quantity + item['quantity'] if not created else item['quantity']
                order_item.product_unit_price = product.price
                order_item.product_total_price = Decimal(product.price * order_item.product_quantity).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP)
                built_items.append(order_item)

                logger.info(
                    f'Updated OrderItem: "{order_item.product_name}" | '
                    f'Old quantity: {order_item.product_quantity - item["quantity"]} | '
                    f'New quantity: {order_item.product_quantity}' if not created else
                    f'Created OrderItem: "{order_item.product_name}"'
                )
            else:
                logger.warning(
                    f'Product "{item["product_name"]}" (pk=#{item["product_pk"]}) does not exist anymore '
                    f'Skipping order_item building for this session_item'
                )
                continue

        if built_items:
            OrderItem.objects.bulk_update(
                built_items,
                fields=[
                    'product_name',
                    'product_image_url',
                    'product_description',
                    'product_quantity',
                    'product_unit_price',
                    'product_total_price',
                ],
            )
            OrderOrchestrationService(order=order).update_price()

    def _handle_backoffice_member_session(self):
        for item in self.session_items.values():
            StockReservationService(cart_item=item).release_reserved_stock()
            logger.info(f'SessionItem "{item["product_name"]}" (pk=#{item["product_pk"]}) '
                        f'was released for a back office member {self.user}')