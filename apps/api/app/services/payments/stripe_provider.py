"""Stripe payment adapter with official SDK signature verification."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from app.services.payments.base import (
    CheckoutSession,
    PaymentProvider,
    PaymentStatus,
    WebhookEvent,
)


class StripeProvider(PaymentProvider):
    name = "stripe"

    def __init__(self) -> None:
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        self.base_url = "https://api.stripe.com/v1"

    def _require_key(self) -> None:
        if not self.secret_key:
            raise RuntimeError(
                "Stripe is not configured. Set STRIPE_SECRET_KEY. "
                "Do not grant entitlements from success URL alone."
            )

    def _stripe_sdk(self):
        try:
            import stripe

            return stripe
        except ImportError as exc:
            raise RuntimeError(
                "Official 'stripe' package is required for production webhook verification. "
                "pip install stripe"
            ) from exc

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
        self._require_key()
        try:
            stripe = self._stripe_sdk()
            stripe.api_key = self.secret_key
            line_item: dict[str, Any] = {
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": amount_cents,
                    "product_data": {"name": "VRAV Tube Engine"},
                },
                "quantity": 1,
            }
            if subscription and interval:
                line_item["price_data"]["recurring"] = {"interval": interval}
            session = stripe.checkout.Session.create(
                mode="subscription" if subscription else "payment",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                line_items=[line_item],
                metadata=metadata or {},
            )
            return CheckoutSession(
                provider=self.name,
                session_id=session.id,
                checkout_url=session.url,
                raw=session.to_dict() if hasattr(session, "to_dict") else None,
            )
        except RuntimeError:
            raise
        except Exception:
            # Fallback HTTP form post if SDK path fails at runtime
            data: dict[str, Any] = {
                "mode": "subscription" if subscription else "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "customer_email": customer_email,
                "line_items[0][price_data][currency]": currency.lower(),
                "line_items[0][price_data][unit_amount]": str(amount_cents),
                "line_items[0][price_data][product_data][name]": "VRAV Tube Engine",
                "line_items[0][quantity]": "1",
            }
            if subscription and interval:
                data["line_items[0][price_data][recurring][interval]"] = interval
            if metadata:
                for k, v in metadata.items():
                    data[f"metadata[{k}]"] = v
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/checkout/sessions",
                    data=data,
                    auth=(self.secret_key, ""),
                )
                if resp.status_code >= 400:
                    raise RuntimeError(f"Stripe checkout failed: {resp.text}")
                body = resp.json()
            return CheckoutSession(
                provider=self.name,
                session_id=body["id"],
                checkout_url=body["url"],
                raw=body,
            )

    async def verify_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        self._require_key()
        if not self.webhook_secret:
            raise RuntimeError("STRIPE_WEBHOOK_SECRET not configured — cannot verify webhooks")
        sig = headers.get("stripe-signature") or headers.get("Stripe-Signature") or ""
        if not sig:
            raise RuntimeError("Missing Stripe-Signature header")
        stripe = self._stripe_sdk()
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig,
                secret=self.webhook_secret,
            )
        except Exception as exc:
            raise RuntimeError(f"Stripe webhook signature verification failed: {exc}") from exc
        body = event.to_dict() if hasattr(event, "to_dict") else dict(event)
        return WebhookEvent(
            provider=self.name,
            event_id=str(body.get("id", "")),
            event_type=str(body.get("type", "")),
            payload=body,
            verified=True,
        )

    async def get_payment_status(self, external_id: str) -> PaymentStatus:
        self._require_key()
        try:
            stripe = self._stripe_sdk()
            stripe.api_key = self.secret_key
            session = stripe.checkout.Session.retrieve(external_id)
            status = getattr(session, "payment_status", None) or getattr(session, "status", None)
        except Exception:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/checkout/sessions/{external_id}",
                    auth=(self.secret_key, ""),
                )
                if resp.status_code >= 400:
                    return PaymentStatus.FAILED
                body = resp.json()
                status = body.get("payment_status") or body.get("status")
        mapping = {
            "paid": PaymentStatus.SUCCEEDED,
            "complete": PaymentStatus.SUCCEEDED,
            "unpaid": PaymentStatus.PENDING,
            "open": PaymentStatus.PENDING,
            "expired": PaymentStatus.EXPIRED,
        }
        return mapping.get(str(status), PaymentStatus.PENDING)
