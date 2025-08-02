from django.utils import timezone

from payments.gateways.mollie import MollieGateway
from core.models import Order, Payment

import logging

logger = logging.getLogger(__name__)


def initiate_payment(order, user_id):
    gateway = MollieGateway()
    session = gateway.create_payment_session(order=order, currency='CHF', user_id=user_id)
    if session is None:
        return None

    payment = Payment.objects.create(
        order=order,
        payment_method=Payment.PaymentMethod.TWINT,
        payment_status=Payment.PaymentStatus.INITIATED,
        transaction=session.session_id,
    )
    return session.checkout_url


def process_webhook(webhook_data: dict):
    transaction_id = webhook_data.get('id')
    try:
        payment = Payment.objects.get(transaction=transaction_id)
    except Payment.DoesNotExist:
        logger.error(f'[ERROR] Webhook received for unknown transaction ID: "{transaction_id}"')
        return None

    gateway = MollieGateway()
    internal_status = gateway.handle_webhook(webhook_data)

    if internal_status == 'succeeded':
        payment.payment_status = Payment.PaymentStatus.SUCCEEDED
        payment.paid_at = timezone.now()

        order = payment.order
        order.status = Order.OrderStatus.PAID
        order.save()
        logger.warning(f'[OK] Successful Payment: #{payment.id} | Transaction ID: "{payment.transaction}" | '
                       f'Status: {payment.payment_status} | Order: #{order.id} | Customer: {order.user}\n')

    elif internal_status == 'initiated':
        payment.payment_status = Payment.PaymentStatus.INITIATED
        logger.error(f'[ERROR] Delayed/Ambiguous Payment: #{payment.id} | Transaction ID: "{payment.transaction}" | '
                     f'Status: {payment.payment_status}\n')

    else:
        payment.payment_status = Payment.PaymentStatus.FAILED
        logger.error(f'[ERROR] Failed Payment: #{payment.id} | Transaction ID: "{payment.transaction}" | '
                     f'Status: {payment.payment_status}\n')

    payment.save()
