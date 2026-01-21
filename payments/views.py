import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from core.domain import OrderStatus
from core.models import Order
from core.services.order_amount_calc import OrderRecalcService
from payments.domain import PaymentMethod
from payments.services.initiate_payment import initiate_payment
from payments.services.process_webhook import process_webhook
from payments.utils import log_webhook_source
from shared.permissions.utils import is_authenticated

logger = logging.getLogger(__name__)


class ReviewOrderView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/review_order.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_methods'] = PaymentMethod.choices

        user = self.request.user.customer_profile
        shipping_info = user.shipping_info
        try:
            order = Order.objects.prefetch_related('items').filter(user=user, status=OrderStatus.PENDING).first()
            if price_diff := OrderRecalcService(order=order).recalculate():
                context['price_diff'] = price_diff

            context['order'] = order
            context['shipping_info'] = shipping_info
        except Exception as exc:
            logger.error(f'Error during order review | exc={exc}')
            context['message'] = 'Something went wrong, try again later'
        return context


def start_checkout(request):
    if not is_authenticated(request):
        return redirect(f"{reverse('accounts:login')}?info=login_required_for_payment")
    return redirect('accounts:shipping_info')


def start_payment(request, pk):
    if not is_authenticated(request):
        return redirect(f"{reverse('accounts:login')}?info=login_required_for_payment")

    order = Order.objects.prefetch_related('items').filter(user=request.user.customer_profile, pk=pk).first()
    if not order:
        return redirect(reverse('payments:something_went_wrong'))

    shipping = getattr(request.user.customer_profile, 'shipping_info', None)
    if not shipping:
        return redirect(reverse('payments:something_went_wrong'))

    payment_method = request.POST.get('payment_method')
    if payment_method not in PaymentMethod:
        return redirect(reverse('payments:something_went_wrong'))

    order.shipping_email = shipping.email
    order.shipping_first_name = shipping.first_name
    order.shipping_last_name = shipping.last_name
    order.shipping_phone = shipping.phone
    order.shipping_country = shipping.country
    order.shipping_city = shipping.city
    order.shipping_postal_code = shipping.postal_code
    order.shipping_street = shipping.street
    order.shipping_house_number = shipping.house_number
    order.shipping_apartment = shipping.apartment
    order.shipping_additional_info = shipping.additional_info
    order.save()

    payment_url = initiate_payment(order=order, user_pk=request.user.pk, payment_method=payment_method)
    if payment_url is not None:
        return redirect(payment_url)
    return redirect(reverse('payments:something_went_wrong'))


@csrf_exempt
@log_webhook_source
def mollie_webhook(request):
    if request.method == 'POST':
        logger.info(f'Content-Type: {request.content_type}')
        try:
            if request.content_type == 'application/json':
                webhook_data = json.loads(request.body)
            else:
                webhook_data = request.POST.dict()
        except Exception:
            logger.error(f'Failed to parse webhook body | Headers: {request.headers}')
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)

        process_webhook(webhook_data)

        return HttpResponse(status=200)
    return HttpResponseNotAllowed(['POST'])