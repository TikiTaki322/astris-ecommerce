from django.db.models import Prefetch
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import ListView

from core.domain import OrderStatus
from core.models import Order
from core.services.stock_reservation import StockReservationService
from payments.models import Payment
from shared.permissions.mixins import AuthRequiredMixin, BackofficeAccessRequiredMixin
from shared.permissions.utils import is_authenticated, is_backoffice_member, is_order_owner
from shared.tasks import send_email_task
from shared.utils import redirect_with_message


class CartClearOutView(View):
    def post(self, request):
        if is_authenticated(request):
            order = (
                Order.objects
                .prefetch_related('items')
                .filter(
                    user=request.user.customer_profile,
                    status=OrderStatus.PENDING
                )
                .first()
            )

            for order_item in order.items.all():
                StockReservationService(cart_item=order_item).release_reserved_stock()
            order.delete()
        else:
            session_order = request.session.get('session_order', {'items': {}})
            for session_item in session_order['items'].values():
                StockReservationService(cart_item=session_item).release_reserved_stock()
            del request.session['session_order']

        return redirect_with_message(
            'core:product_list',
            cart_clear_out=True,
            message="Cart's been cleared"
        )


class OrderListView(AuthRequiredMixin, ListView):
    template_name = 'core/order_list.html'
    context_object_name = 'orders'

    # VISIBLE_STATUSES = ['pending', 'paid', 'shipped', 'delivered', 'expired']

    def get_queryset(self):
        # initial_qs = Order.objects.prefetch_related(
        #     Prefetch('payments', queryset=Payment.objects.order_by('-created_at')),
        #     Prefetch('user', queryset=CustomerProfile.objects.select_related('user')),
        #     'items'
        # )
        # have to test both queries with Silk

        initial_qs = (
            Order.objects
            .select_related('user')
            .prefetch_related(
                Prefetch('payments', queryset=Payment.objects.order_by('-created_at')),
                'items'
            )
        )
        qs = initial_qs.exclude(status__in=['pending', 'expired'])

        status = self.request.GET.get('status')
        if status:
            qs = (
                (initial_qs if status.lower() in ('pending', 'expired') else qs)
                .filter(status=status)
            )

        date_str = self.request.GET.get('date')
        if date_str:
            date = parse_date(date_str)
            if date:
                qs = qs.filter(created_at__date=date)

        user = self.request.user
        if not is_backoffice_member(self.request):
            qs = qs.filter(user=user.customer_profile)

        return qs.order_by('-updated_at', '-pk', '-paid_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_statuses = [choice[0] for choice in OrderStatus.choices]

        # if not is_backoffice_member(self.request):
        #     all_statuses = [choice for choice in all_statuses if choice not in self.ADMIN_STATUSES]

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
            update_fields = ['status']
            if is_backoffice_member(request):
                # Manager-flow
                update_fields.append('shipped_at')
                if order.status == OrderStatus.PAID:
                    order.status = OrderStatus.SHIPPED
                    order.shipped_at = timezone.now()
                    message = f'Order #{order.pk} by {order.user} marked as shipped'

                    if tracking_info := request.POST.get('tracking_info'):
                        order.tracking_info = tracking_info
                        update_fields.append('tracking_info')
                        message += '. Tracking Number has been added'

                elif order.status == OrderStatus.SHIPPED:
                    order.status = OrderStatus.PAID
                    order.shipped_at = None
                    message = f'Order #{order.pk} by {order.user} returned to paid'

                    if order.tracking_info:
                        order.tracking_info = None
                        update_fields.append('tracking_info')
                        message += ' Tracking Number has been deleted'

            elif is_order_owner(request, order):
                # Buyer-flow
                update_fields.append('delivered_at')
                if order.status == OrderStatus.SHIPPED and not order.delivered_at:
                    order.status = OrderStatus.DELIVERED
                    order.delivered_at = timezone.now()
                    message = f'Order #{order.pk} marked as delivered. Thank you for choosing us!'

            order.save(update_fields=update_fields)
            response = {'success': True, 'message': message}

        except Order.DoesNotExist:
            response = {'success': False, 'message': 'This order does not exist anymore'}

        return redirect_with_message(
            'core:order_list',
            filters=filters,
            status_changed=response.get('success', None),
            message=response.get('message', None),
        )


class OrderNotifyShippedView(BackofficeAccessRequiredMixin, View):
    def post(self, request, pk):
        filters = {
            'status': request.POST.get('status'),
            'date': request.POST.get('date'),
        }

        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            response = {'success': False, 'message': f'Invalid Order #{pk}'}
            return redirect_with_message(
                'core:order_list',
                filters=filters,
                notification_sent=response.get('success', None),
                message=response.get('message', None),
            )

        if order.status != OrderStatus.SHIPPED:
            response = {'success': False, 'message': f'Order #{order.pk} has to be shipped at first'}
            return redirect_with_message(
                'core:order_list',
                filters=filters,
                notification_sent=response.get('success', None),
                message=response.get('message', None),
            )
        order.notified_at = timezone.now()
        order.save(update_fields=['notified_at'])

        context = {'order_pk': order.pk}
        send_email_task.delay(
            email_type='order_shipped',
            to_emails=order.shipping_email,
            context=context
        )

        response = {'success': True, 'message': f'Shipment notification initiated to "{order.shipping_email}"'}

        return redirect_with_message(
            'core:order_list',
            filters=filters,
            notification_sent=response.get('success', None),
            message=response.get('message', None),
        )