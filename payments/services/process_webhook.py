import logging

from django.utils import timezone

from core.domain import OrderStatus
from payments.domain import PaymentStatus
from payments.models import Payment
from .gateway_resolver import resolve_gateway

logger = logging.getLogger(__name__)


def process_webhook(webhook_data: dict):
    transaction_id = webhook_data.get('id', None)
    try:
        payment = Payment.objects.get(transaction=transaction_id)
    except Payment.DoesNotExist:
        logger.error(f'Webhook received for unknown transaction ID: "{transaction_id}"')
        return None

    gateway = resolve_gateway(payment.payment_method)
    internal_status = gateway.handle_webhook(webhook_data)

    if internal_status == 'succeeded':
        payment.payment_status = PaymentStatus.SUCCEEDED
        payment.paid_at = timezone.now()

        order = payment.order
        order.status = OrderStatus.PAID
        order.paid_at = payment.paid_at
        order.save(update_fields=['status', 'paid_at'])
        logger.info(f'Successful Payment: #{payment.pk} | Transaction ID: "{payment.transaction}" | '
                    f'Status: {payment.payment_status} | Order: #{order.pk} | Customer: {order.user}')

    elif internal_status == 'initiated':
        payment.payment_status = PaymentStatus.INITIATED
        logger.error(f'Delayed/Ambiguous Payment: #{payment.pk} | Transaction ID: "{payment.transaction}" | '
                     f'Status: {payment.payment_status}')

    else:
        payment.payment_status = PaymentStatus.FAILED
        logger.error(f'Failed Payment: #{payment.pk} | Transaction ID: "{payment.transaction}" | '
                     f'Status: {payment.payment_status}')

    payment.save()