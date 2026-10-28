"""Payment provider abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass
class CheckoutSession:
    provider: str
    session_id: str
    checkout_url: str
    raw: Optional[dict[str, Any]] = None


@dataclass
class WebhookEvent:
    provider: str
    event_id: str
    event_type: str
    payload: dict[str, Any]
    verified: bool


class PaymentProvider(ABC):
    name: str

    @abstractmethod
    async def create_checkout_session(
        self,
        *,
        amount_cents: int,
        currency: str,
        customer_email: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[dict[str, str]] = None,
        subscription: bool = False,
        interval: Optional[str] = None,
    ) -> CheckoutSession:
        ...

    @abstractmethod
    async def verify_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        ...

    @abstractmethod
    async def get_payment_status(self, external_id: str) -> PaymentStatus:
        ...
