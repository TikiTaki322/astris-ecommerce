from abc import ABC, abstractmethod
from decimal import Decimal
from payments.types import PaymentSession


class PaymentGateway(ABC):
    @abstractmethod
    def create_payment_session(self, amount: Decimal, currency: str, user_id: int) -> PaymentSession:
        pass

    @abstractmethod
    def handle_webhook(self, webhook_data: dict) -> str:
        pass

    @abstractmethod
    def check_payment_status(self, transaction_id: str) -> str:
        pass