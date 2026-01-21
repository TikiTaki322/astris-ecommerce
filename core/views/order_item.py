from decimal import Decimal, ROUND_HALF_UP

from django.views import View
from django.views.generic import TemplateView

from core.domain import OrderStatus
from core.models import Order, OrderItem, DeliverySettings
from core.services.order_amount_calc import OrderOrchestrationService
from core.services.stock_reservation import StockReservationService
from shared.permissions.utils import is_authenticated
from shared.utils import redirect_with_message


class OrderItemListView(TemplateView):
    template_name = 'core/order_item_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_item_addition'] = self.request.GET.get('order_item_addition')
        context['order_item_deletion'] = self.request.GET.get('order_item_deletion')
        context['message'] = self.request.GET.get('message')
        context['settings'] = DeliverySettings.load()

        if is_authenticated(self.request):
            context.update(self._get_db_order_context())
        else:
            context.update(self._get_session_order_context())
        return context

    def _get_db_order_context(self):
        context = {}
        order = (
            Order.objects
            .prefetch_related('items')
            .filter(
                user=self.request.user.customer_profile,
                status=OrderStatus.PENDING
            )
            .first()
        )

        if order:
            context['order'] = order
        return context

    def _get_session_order_context(self):
        context = {}
        if session_order := self.request.session.get('session_order', {}):
            context['session_order'] = session_order
            context['session_order_delivery_amount'] = Decimal(session_order['delivery_amount'])
        return context


class OrderItemCreateView(View):
    def post(self, request, pk):
        response = StockReservationService(product_pk=pk).reserve_stock()
        if product := response.get('product', None):

            if is_authenticated(request):
                order, _ = Order.objects.get_or_create(user=request.user.customer_profile, status=OrderStatus.PENDING)
                order_item, created = OrderItem.objects.get_or_create(
                    order=order,
                    product_pk_snapshot=product.pk,
                    defaults={
                        'product_name': product.name,
                        'product_unit_price': product.price,
                        'product_total_price': product.price,
                        'product_description': product.description,
                        'product_image_url': product.primary_image_url
                    }
                )
                if not created:
                    order_item.product_quantity += 1
                    order_item.product_total_price = Decimal(product.price * order_item.product_quantity).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )
                    order_item.save(update_fields=['product_quantity', 'product_total_price'])

                OrderOrchestrationService(order=order).update_price()

            else:
                pk = str(pk)
                session_order = request.session.get('session_order', {'items': {}}).copy()

                if pk in session_order['items']:
                    quantity = session_order['items'][pk]['quantity'] + 1
                    total_price = Decimal(product.price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    session_order['items'][pk].update({'quantity': quantity, 'total_price': str(total_price)})
                else:
                    session_order['items'][pk] = {
                        'product_pk': product.pk,
                        'product_name': product.name,
                        'description': product.description,
                        'quantity': 1,
                        'unit_price': str(product.price),
                        'total_price': str(product.price),
                        'product_image_url': product.primary_image_url
                    }

                session_order = OrderOrchestrationService(session_order=session_order).update_price()
                request.session['session_order'] = session_order
                request.session.modified = True

        return redirect_with_message(
            # 'core:orderitem_list',
            'core:product_list',
            order_item_addition=response.get('success', None),
            message=response.get('message', None)
        )


class OrderItemUpdateView(View):
    pass


class OrderItemDeleteView(View):
    def post(self, request, pk):
        response = {'success': False, 'message': 'Nothing to delete.'}
        if is_authenticated(request):
            if order_item := OrderItem.objects.filter(pk=pk).first():
                response = StockReservationService(cart_item=order_item).release_reserved_stock()
                order_item.delete()

            order = (
                Order.objects
                .prefetch_related('items')
                .filter(
                    user=request.user.customer_profile,
                    status=OrderStatus.PENDING
                )
                .first()
            )
            if not order.items.exists():
                order.delete()
            else:
                OrderOrchestrationService(order=order).update_price()

        else:
            session_order = request.session.get('session_order', {'items': {}})
            if session_item := session_order['items'].get(f'{str(pk)}', None):
                response = StockReservationService(cart_item=session_item).release_reserved_stock()
                del session_order['items'][str(pk)]

                if not session_order['items']:
                    del request.session['session_order']
                else:
                    session_order = OrderOrchestrationService(session_order=session_order).update_price()
                    request.session['session_order'] = session_order
                    request.session.modified = True

        return redirect_with_message(
            'core:orderitem_list',
            order_item_deletion=response.get('success', None),
            message=response.get('message', None)
        )