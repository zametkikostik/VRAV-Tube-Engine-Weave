# Payments

## Providers

| Provider | Markets | Env keys |
|----------|---------|----------|
| Stripe | International | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` |
| YooKassa | Russia / CIS | `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` |

## Critical rule

**Entitlements activate only after a verified payment webhook**, never from the success URL alone.

## Flow

1. Client calls `POST /api/v1/billing/checkout`
2. User pays on provider-hosted page
3. Provider sends webhook → `POST /api/v1/webhooks/stripe` or `/yookassa`
4. Signature verification → idempotent `process_verified_webhook` → subscription ACTIVE

## Webhook URLs

- Stripe: `https://your.domain/api/v1/webhooks/stripe`
- YooKassa: `https://your.domain/api/v1/webhooks/yookassa`

## Plans

`personal` · `professional` · `agency` · `enterprise` — limits in `app.services.entitlements.PLAN_LIMITS`.
