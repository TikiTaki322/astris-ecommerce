from django.shortcuts import render, redirect, reverse
from django.template.loader import render_to_string

from django.views.generic import TemplateView, ListView, DetailView
from django.views import View

from core.services.order_price_sync import OrderPriceSyncService
from core.services.stock_reservation import StockReservationService
from core.models import Product, Order, OrderItem

from accounts.services.email_sender import send_email_via_resend

from shared.permissions.utils import is_authenticated, is_staff_or_seller, is_order_owner
from shared.permissions.mixins import AuthRequiredMixin, StaffOrSellerRequiredMixin
from shared.utils import redirect_with_message

from django.utils.dateparse import parse_date
from django.utils import timezone

from decimal import Decimal, ROUND_HALF_UP

import logging

logger = logging.getLogger(__name__)


class OrderItemListView(TemplateView):
    template_name = 'core/order_item_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_item_addition'] = self.request.GET.get('order_item_addition')
        context['order_item_deletion'] = self.request.GET.get('order_item_deletion')
        context['message'] = self.request.GET.get('message')

        if is_authenticated(self.request):
            context.update(self._get_authenticated_order_context())
        else:
            context.update(self._get_session_order_context())
        return context

    def _get_authenticated_order_context(self):
        context = {}
        if order := Order.objects.filter(user=self.request.user.customer_profile, status=Order.OrderStatus.PENDING).first():
            service = OrderPriceSyncService(order=order)
            context['price_diff'] = service.sync() or order.price_diff
            order.price_diff = False

            if order.items.exists():
                order.amount = service.get_amount()
                order.save(update_fields=['amount', 'price_diff'])
                context['order'] = order
            else:
                order.delete()
        return context

    def _get_session_order_context(self):
        context = {}
        if session_order := self.request.session.get('session_order', {}):
            service = OrderPriceSyncService(session_order=session_order)
            context['price_diff'] = service.sync()
            context['amount'] = service.get_amount()
            context['session_order'] = service.session_order
            self.request.session['session_order'] = service.session_order
        return context


class OrderItemCreateView(View):
    def post(self, request, pk):
        response = StockReservationService(product_pk=pk).reserve_stock()
        if product := response.get('product', None):

            if is_authenticated(request):
                order, _ = Order.objects.get_or_create(user=request.user.customer_profile, status=Order.OrderStatus.PENDING)
                order_item, created = OrderItem.objects.get_or_create(order=order, product_id_snapshot=product.pk)
                if not created:
                    order_item.product_quantity += 1
                order_item.product_id_snapshot = product.pk
                order_item.product_name = product.name
                order_item.product_description = product.description
                order_item.product_unit_price = product.price
                order_item.product_total_price = Decimal(product.price * order_item.product_quantity).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP)
                order_item.save()
            else:
                pk = str(pk)
                session_order = request.session.get('session_order', {})
                session_order[pk] = session_order.get(pk, {})
                session_order[pk]['product_pk'] = product.pk
                session_order[pk]['product_name'] = product.name
                session_order[pk]['description'] = product.description
                session_order[pk]['quantity'] = session_order[pk].get('quantity', 0) + 1
                session_order[pk]['unit_price'] = str(product.price)
                session_order[pk]['total_price'] = str(Decimal(product.price * session_order[pk]['quantity']))
                request.session['session_order'] = session_order

        return redirect_with_message(
            'core:orderitem_list',
            order_item_addition=response.get('success', None),  # True/False
            message=response.get('message', None)
        )


class OrderItemUpdateView(View):
    pass


class OrderItemDeleteView(View):
    def post(self, request, pk):
        response = {'success': False, 'message': 'Nothing to delete.'}
        if is_authenticated(request):
            if order_item := OrderItem.objects.filter(pk=pk).first():
                response = StockReservationService(cart_item=order_item).release_reserved_stock()  # Releasing order_item quantity to the stock
                order_item.delete()
        else:
            session_order = request.session.get('session_order', {})
            if session_item := session_order.get(f'{str(pk)}', None):
                response = StockReservationService(cart_item=session_item).release_reserved_stock()  # Releasing session_item quantity to the stock
                del session_order[str(pk)]
                request.session['session_order'] = session_order

        return redirect_with_message(
            'core:orderitem_list',
            order_item_deletion=response.get('success', None),  # True/False
            message=response.get('message', None)
        )


class OrderListView(AuthRequiredMixin, ListView):
    template_name = 'core/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.all().prefetch_related('items')

        if not is_staff_or_seller(self.request):
            qs = qs.filter(user=user.customer_profile, status__in=['paid', 'shipped', 'delivered'])

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        date_str = self.request.GET.get('date')
        if date_str:
            date = parse_date(date_str)
            if date:
                qs = qs.filter(created_at__date=date)

        return qs.order_by('-updated_at', '-pk', '-paid_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        admin_statuses = ['pending', 'cancelled']
        all_statuses = [choice[0] for choice in Order.OrderStatus.choices]

        if not is_staff_or_seller(self.request):
            all_statuses = [choice for choice in all_statuses if choice not in admin_statuses]

        context['statuses'] = all_statuses
        context['selected_status'] = self.request.GET.get('status') or ''

        context['notification_sent'] = self.request.GET.get('notification_sent')
        context['status_changed'] = self.request.GET.get('status_changed')
        context['message'] = self.request.GET.get('message')
        return context


class OrderChangeStatusView(AuthRequiredMixin, View):
    def post(self, request, pk):
        filters = {
            'status': request.POST.get('status'),
            'date': request.POST.get('date'),
        }

        try:
            order = Order.objects.get(pk=pk)
            update_fields = ['status', 'updated_at']
            if is_staff_or_seller(request):
                # Manager-flow
                update_fields.append('shipped_at')
                if order.status == Order.OrderStatus.PAID:
                    order.status = Order.OrderStatus.SHIPPED
                    order.shipped_at = timezone.now()
                    message = f'Order #{order.pk} by {order.user} marked as shipped.'

                    if tracking_info := request.POST.get('tracking_info'):
                        order.tracking_info = tracking_info
                        update_fields.append('tracking_info')
                        message += ' Tracking Number has been added.'

                elif order.status == Order.OrderStatus.SHIPPED:
                    order.status = Order.OrderStatus.PAID
                    order.shipped_at = None
                    message = f'Order #{order.pk} by {order.user} returned to paid.'

                    if order.tracking_info:
                        order.tracking_info = None
                        update_fields.append('tracking_info')
                        message += ' Tracking Number has been deleted.'

            elif is_order_owner(request, order):
                # Buyer-flow
                update_fields.append('delivered_at')
                if order.status == Order.OrderStatus.SHIPPED and not order.delivered_at:
                    order.status = Order.OrderStatus.DELIVERED
                    order.delivered_at = timezone.now()
                    message = f'Order #{order.pk} marked as delivered. Thank you!'

            order.save(update_fields=update_fields)
            response = {'success': True, 'message': message}

        except Order.DoesNotExist:
            response = {'success': False, 'message': 'This order does not exist anymore'}
            logger.warning(f'Order #{pk} does not exist.\n\n')

        return redirect_with_message(
            'core:order_list',
            filters=filters,
            status_changed=response.get('success', None),
            message=response.get('message', None),
        )


class OrderNotifyShippedView(StaffOrSellerRequiredMixin, View):
    def post(self, request, pk):
        filters = {
            'status': request.POST.get('status'),
            'date': request.POST.get('date'),
        }

        try:
            order = Order.objects.get(pk=pk)
            if order.status != Order.OrderStatus.SHIPPED:
                response = {'success': False, 'message': f'Order #{order.pk} has to be shipped at first.'}
                return redirect_with_message(
                    'core:order_list',
                    filters=filters,
                    notification_sent=response.get('success', None),
                    message=response.get('message', None),
                )
        except Order.DoesNotExist:
            response = {'success': False, 'message': f'Invalid Order (pk={pk})'}
            return redirect_with_message(
                'core:order_list',
                filters=filters,
                notification_sent=response.get('success', None),
                message=response.get('message', None),
            )

        html_content = render_to_string('emails/shipping_notification.html', {'order': order})
        text_content = render_to_string('emails/shipping_notification.txt', {'order': order})

        try:
            send_email_via_resend(
                to_emails=order.shipping_email,
                subject=f'Order #{order.pk} is on its way to you!',
                html_content=html_content,
                text_content=text_content
            )
            order.notified_at = timezone.now()
            order.save(update_fields=['notified_at', 'updated_at'])
            response = {'success': True, 'message': f'Order #{order.pk} was shipped. '
                                                    f'Customer "{order.user}" notified. '
                                                    f'Email sent to "{order.shipping_email}".'}

        except Exception as e:
            response = {'success': False, 'message': f'Sending shipping notification to email "{order.shipping_email}" failed.'}
            logger.warning(f'Shipping notification failed: {order.shipping_email} | {e}\n\n')

        return redirect_with_message(
            'core:order_list',
            filters=filters,
            notification_sent=response.get('success', None),
            message=response.get('message', None),
        )


""" In case of use in the near future """
# class OrderDetailView(AuthRequiredMixin, DetailView):
#     template_name = 'core/order_detail_FROZEN.html'
#     context_object_name = 'order'
#
#     def dispatch(self, request, *args, **kwargs):
#         if not self.get_queryset().exists():
#             return redirect(reverse('shared:permission_denied'))
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_queryset(self):
#         order_pk = self.kwargs['pk']
#         user = self.request.user
#         qs = Order.objects.prefetch_related('items')
#
#         if is_staff_or_seller(self.request):
#             return qs.filter(pk=order_pk)
#         else:
#             return qs.filter(pk=order_pk, user=user.customer_profile)