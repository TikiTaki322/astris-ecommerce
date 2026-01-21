from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone

from core.models import DeliverySettings
from .order_item_price_sync import OrderItemPriceSyncService


class OrderOrchestrationService:
    def __init__(self, order=None, session_order=None):
        self.order = order
        self.session_order = session_order

        self.calc = OrderCalcService(
            order=order,
            session_items=session_order.get('items', None) if session_order else None
        )

    def update_price(self):
        if self.order:
            items_amount = self.calc.get_items_amount()
            self.order.items_amount = items_amount
            self.order.delivery_amount = self.calc.get_delivery_amount(items_amount)
            self.order.total_amount = self.calc.get_total_amount(items_amount)
            self.order.save(update_fields=['items_amount', 'delivery_amount', 'total_amount', 'updated_at'])
            return self.order

        elif self.session_order:
            items_amount = self.calc.get_items_amount()  # returns Decimal
            self.session_order['items_amount'] = str(items_amount)
            self.session_order['delivery_amount'] = str(self.calc.get_delivery_amount(items_amount))
            self.session_order['total_amount'] = str(self.calc.get_total_amount(items_amount))
            self.session_order['modified_at'] = timezone.now().isoformat()
            return self.session_order


class OrderCalcService:
    def __init__(self, order=None, session_items=None):
        self.order = order
        self.session_items = session_items
        self.delivery_settings = DeliverySettings.load()

    def get_items_amount(self) -> Decimal:
        if self.order:
            total = self.order.items.aggregate(items_amount=Sum('product_total_price'))['items_amount'] or Decimal('0.00')
        elif self.session_items:
            total = sum(Decimal(item['total_price']) for item in self.session_items.values())
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_delivery_amount(self, items_amount: Decimal) -> Decimal:
        return self.delivery_settings.delivery_price if items_amount < self.delivery_settings.delivery_threshold else Decimal('0.00')

    def get_total_amount(self, items_amount: Decimal) -> Decimal:
        return items_amount + self.get_delivery_amount(items_amount)


class OrderRecalcService:
    def __init__(self, order):
        self.order = order

    def recalculate(self) -> bool:
        if price_diff := OrderItemPriceSyncService(order=self.order).sync():
            OrderOrchestrationService(order=self.order).update_price()
        return price_diff