from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed, Http404
from django.urls import reverse

from core.models import Order
from accounts.models import ShippingInfo
from core.services.payments import initiate_payment, process_webhook

from shared.permissions.utils import is_authenticated
from payments.utils import log_webhook_source

import json
import logging

logger = logging.getLogger(__name__)


def start_checkout(request):
    if not is_authenticated(request):
        return redirect(f"{reverse('accounts:login')}?info=login_required_for_payment")
    return redirect('accounts:shipping_info')


def start_payment(request, pk):
    if not is_authenticated(request):
        return redirect(f"{reverse('accounts:login')}?info=login_required_for_payment")

    order = get_object_or_404(Order, pk=pk)

    shipping = getattr(request.user.customer_profile, 'shipping_info', None)
    if not shipping:
        return redirect(f"{reverse('accounts:shipping_info')}?info=shipping_required")

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

    payment_url = initiate_payment(order, user_id=request.user.id)
    if payment_url is not None:
        return redirect(payment_url)
    return redirect('payments:failed')


@csrf_exempt
@log_webhook_source
def mollie_webhook(request):
    if request.method == 'POST':
        logger.warning(f'[INFO] Content-Type: {request.content_type}\n')
        try:
            if request.content_type == 'application/json':
                mollie_webhook_data = json.loads(request.body)
            else:
                mollie_webhook_data = request.POST.dict()
        except Exception:
            logger.error(f'[ERROR] Failed to parse webhook body | Headers: {request.headers}')
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        process_webhook(mollie_webhook_data)
        return HttpResponse(status=200)
    return HttpResponseNotAllowed(['POST'])


class ReviewOrderView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/review_order.html'

    # def dispatch(self, request, *args, **kwargs):
    #     try:
    #         _ = request.user.customer_profile.shipping_info
    #     except ShippingInfo.DoesNotExist:
    #         return redirect('accounts:shipping_info')
    #     return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user.customer_profile
        try:
            order = Order.objects.get(user=user, status=Order.OrderStatus.PENDING)
        except Order.DoesNotExist:
            raise Http404('No active order')

        context['order'] = order
        context['shipping_info'] = user.shipping_info
        return context


