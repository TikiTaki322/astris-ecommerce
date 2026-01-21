from abc import ABC, abstractmethod
from typing import Literal

from payments.types import PaymentSession


class PaymentGateway(ABC):
    @abstractmethod
    def create_payment_session(self, order, user_id: int, payment_method: str,
                               currency: Literal['CHF', 'EUR', 'USD']) -> PaymentSession:
        pass

    @abstractmethod
    def handle_webhook(self, webhook_data: dict) -> str:
        pass

    @abstractmethod
    def check_payment_status(self, transaction_id: str) -> str:
        pass
