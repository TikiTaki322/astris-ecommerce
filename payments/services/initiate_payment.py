from payments.domain import PaymentStatus
from payments.models import Payment
from .gateway_resolver import resolve_gateway


def initiate_payment(order, user_pk, payment_method):
    gateway = resolve_gateway(payment_method)
    session = gateway.create_payment_session(order=order, user_id=user_pk, payment_method=payment_method)
    if session is None:
        return None

    Payment.objects.create(
        order=order,
        payment_method=payment_method,
        payment_status=PaymentStatus.INITIATED,
        transaction=session.session_id,
    )
    return session.checkout_url
