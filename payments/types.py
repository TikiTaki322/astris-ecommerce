from dataclasses import dataclass


@dataclass
class PaymentSession:
    session_id: str
    checkout_url: str
