# Production readiness

## Implemented

- [x] Multi-tenant auth (JWT access + refresh)
- [x] Organizations / tenants / RBAC membership
- [x] Video intake (YouTube URL, transcript, metadata)
- [x] Audit jobs with AI gateway (RouterAI / OpenRouter / xAI) + offline mode
- [x] HTML + PDF report export
- [x] Stripe + YooKassa checkout + verified webhooks
- [x] Entitlements server-side
- [x] Admin stats / users / contact leads
- [x] White-label settings API
- [x] YouTube OAuth (server-side tokens)
- [x] Alembic migrations 001–005
- [x] Docker Compose + release GitHub Actions
- [x] i18n EN / RU / BG

## Before first paid customer

- [ ] Real `APP_SECRET_KEY` and DB passwords
- [ ] HTTPS reverse proxy
- [ ] Stripe/YooKassa live keys + webhook secrets
- [ ] RouterAI or OpenRouter key
- [ ] Google OAuth for YouTube (optional)
- [ ] Email verification / password reset (deferred)
- [ ] Rate limits tuned for production traffic
- [ ] Monitoring / log aggregation

## Legal

- Advisory reports only — not affiliated with YouTube/Google
- No fabricated monetization guarantees
- Commercial license: see `COMMERCIAL_LICENSE.md`
