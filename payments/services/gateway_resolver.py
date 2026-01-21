from payments.domain import PaymentMethod
from payments.services.gateways import MollieGateway


def resolve_gateway(payment_method):
    GATEWAYS = {
        PaymentMethod.TWINT: MollieGateway(),
        # PaymentMethod.CARD: SomeCardGateway(),
        # PaymentMethod.CRYPTO: CryptoGateway(),
    }
    gateway = GATEWAYS.get(payment_method, None)
    return gateway