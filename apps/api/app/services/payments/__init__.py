from app.services.payments.base import (
    CheckoutSession,
    PaymentProvider,
    PaymentStatus,
    WebhookEvent,
)
from app.services.payments.stripe_provider import StripeProvider
from app.services.payments.yookassa_provider import YooKassaProvider


def get_payment_provider(name: str) -> PaymentProvider:
    if name == "stripe":
        return StripeProvider()
    if name == "yookassa":
        return YooKassaProvider()
    raise ValueError(f"Unknown payment provider: {name}")


__all__ = [
    "PaymentProvider",
    "PaymentStatus",
    "CheckoutSession",
    "WebhookEvent",
    "StripeProvider",
    "YooKassaProvider",
    "get_payment_provider",
]
