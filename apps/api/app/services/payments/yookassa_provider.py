"""YooKassa payment adapter (Russian market).

Official docs: https://yookassa.ru/developers
Requires YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY.
"""

import base64
import json
import os
from typing import Any, Optional
from uuid import uuid4

import httpx

from app.services.payments.base import (
    CheckoutSession,
    PaymentProvider,
    PaymentStatus,
    WebhookEvent,
)


class YooKassaProvider(PaymentProvider):
    name = "yookassa"

    def __init__(self) -> None:
        self.shop_id = os.getenv("YOOKASSA_SHOP_ID", "")
        self.secret_key = os.getenv("YOOKASSA_SECRET_KEY", "")
        self.base_url = "https://api.yookassa.ru/v3"

    def _require_credentials(self) -> None:
        if not self.shop_id or not self.secret_key:
            raise RuntimeError(
                "YooKassa is not configured. Set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY. "
                "Merchant eligibility must be verified separately."
            )

    def _auth_header(self) -> str:
        token = base64.b64encode(f"{self.shop_id}:{self.secret_key}".encode()).decode()
        return f"Basic {token}"

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
        self._require_credentials()
        value = f"{amount_cents / 100:.2f}"
        payload: dict[str, Any] = {
            "amount": {"value": value, "currency": currency.upper()},
            "confirmation": {"type": "redirect", "return_url": success_url},
            "capture": True,
            "description": "VRAV Tube Engine",
            "metadata": metadata or {},
        }
        if customer_email:
            payload["receipt"] = {
                "customer": {"email": customer_email},
                "items": [
                    {
                        "description": "VRAV Tube Engine subscription",
                        "quantity": "1",
                        "amount": {"value": value, "currency": currency.upper()},
                        "vat_code": 1,
                    }
                ],
            }

        idempotence_key = str(uuid4())
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/payments",
                json=payload,
                headers={
                    "Authorization": self._auth_header(),
                    "Idempotence-Key": idempotence_key,
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"YooKassa error: {resp.status_code} {resp.text[:300]}")
            body = resp.json()

        confirmation = body.get("confirmation") or {}
        return CheckoutSession(
            provider=self.name,
            session_id=body["id"],
            checkout_url=confirmation.get("confirmation_url") or success_url,
            raw=body,
        )

    async def verify_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        self._require_credentials()
        body = json.loads(payload.decode("utf-8"))
        obj = body.get("object") or {}
        return WebhookEvent(
            provider=self.name,
            event_id=body.get("event", "") + ":" + str(obj.get("id", "")),
            event_type=body.get("event", ""),
            payload=body,
            verified=False,
        )

    async def get_payment_status(self, external_id: str) -> PaymentStatus:
        self._require_credentials()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.base_url}/payments/{external_id}",
                headers={"Authorization": self._auth_header()},
            )
            if resp.status_code >= 400:
                return PaymentStatus.FAILED
            body = resp.json()
            status = body.get("status")
            mapping = {
                "pending": PaymentStatus.PENDING,
                "waiting_for_capture": PaymentStatus.PENDING,
                "succeeded": PaymentStatus.SUCCEEDED,
                "canceled": PaymentStatus.CANCELLED,
            }
            return mapping.get(status, PaymentStatus.PENDING)
