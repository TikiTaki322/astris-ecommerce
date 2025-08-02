from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.views import View

from core.services.order_price_sync import OrderPriceSyncService
from core.services.inventory import release_product_resources
from core.models import Product, Order, OrderItem

from shared.utils import redirect_with_message, is_authenticated_user
from django.utils.dateparse import parse_date

from decimal import Decimal


class OrderItemListView(TemplateView):
    template_name = 'core/order_item_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_item_addition'] = self.request.GET.get('order_item_addition')
        context['order_item_deletion'] = self.request.GET.get('order_item_deletion')
        context['message'] = self.request.GET.get('message')

        if is_authenticated_user(self.request):
            context.update(self._get_authenticated_order_context())
        else:
            context.update(self._get_session_order_context())
        return context

    def _get_authenticated_order_context(self):
        context = {}
        order = Order.objects.filter(user=self.request.user.customer_profile, status=Order.OrderStatus.PENDING).first()
        if order:
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
        session_order = self.request.session.get('session_order', {})
        if session_order:
            service = OrderPriceSyncService(session_order=session_order)
            context['price_diff'] = service.sync()
            context['amount'] = service.get_amount()
            context['session_order'] = service.session_order
            self.request.session['session_order'] = service.session_order
        return context


class OrderItemCreateView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.quantity -= 1
        if is_in_stock := not bool(product.quantity < 0):
            product.save()

            if is_authenticated_user(request):
                order, _ = Order.objects.get_or_create(user=request.user.customer_profile, status=Order.OrderStatus.PENDING)
                order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
                if not created:
                    order_item.quantity += 1
                order_item.unit_price = product.price
                order_item.price = Decimal(product.price * order_item.quantity)
                order_item.save()
            else:
                pk = str(pk)
                session_order = request.session.get('session_order', {})
                session_order[pk] = session_order.get(pk, {})
                session_order[pk]['product_pk'] = product.pk
                session_order[pk]['product_name'] = product.name
                session_order[pk]['quantity'] = session_order[pk].get('quantity', 0) + 1
                session_order[pk]['unit_price'] = str(product.price)
                session_order[pk]['price'] = str(Decimal(product.price * session_order[pk]['quantity']))
                request.session['session_order'] = session_order

        return redirect_with_message(
            'core:orderitem_list',
            order_item_addition='1' if is_in_stock else '0',
            message='Item was added.' if is_in_stock else f'Unfortunately "{product.name}" is out of stock.'
        )


class OrderItemUpdateView(View):
    pass


class OrderItemDeleteView(View):
    def post(self, request, pk):
        if is_authenticated_user(request):
            order_item = OrderItem.objects.filter(pk=pk).first()
            if is_order_contains_item := bool(order_item):
                release_product_resources(order_item)  # Returning quantity of product to stock
                order_item.delete()
        else:
            session_order = request.session.get('session_order', {})
            key = str(pk)
            if is_order_contains_item := key in session_order:
                release_product_resources(session_order[key])  # Returning quantity of product to stock
                del session_order[key]
                request.session['session_order'] = session_order

        return redirect_with_message(
            'core:orderitem_list',
            order_item_deletion='1' if is_order_contains_item else '0',
            message='Item was removed.' if is_order_contains_item else 'Item not found in the cart.'
        )


class OrderListView(ListView):
    template_name = 'core/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.all().prefetch_related('items', 'items__product')

        if not (self.request.user.is_staff or self.request.user.role == 'seller'):
            qs = qs.filter(user=user.customer_profile, status__in=['paid', 'shipped', 'delivered'])

        status = self.request.GET.get('status')
        all_statuses = [choice[0] for choice in Order.OrderStatus.choices]
        if status and status in all_statuses:
            qs = qs.filter(status=status)

        date_str = self.request.GET.get('date')
        if date_str:
            date = parse_date(date_str)
            if date:
                qs = qs.filter(created_at__date=date)

        return qs.order_by('status', '-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admin_statuses = ['pending', 'cancelled']
        all_statuses = [choice[0] for choice in Order.OrderStatus.choices]

        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.role == 'seller')):
            all_statuses = [choice for choice in all_statuses if choice not in admin_statuses]

        context['statuses'] = all_statuses
        context['selected_status'] = self.request.GET.get('status')
        return context


class OrderDetailView(DetailView):
    template_name = 'core/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.prefetch_related('items', 'items__product')

        if user.is_staff or user.role == 'seller':
            return qs
        return qs.filter(user=user.customer_profile)