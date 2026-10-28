# Release notes — v0.1.0-beta

**Product:** VRAV Tube Engine  
**Date:** 2026-10-28  
**Status:** Production-capable commercial beta (operator verification required)

## Summary

First beta suitable for internal pilots and early agency trials on a VDS with Docker.

## What works out of the box (no external keys)

- Register / login
- Create project → video (manual metadata) → audit job
- Offline structural findings + SEO action items
- HTML report export
- Multilingual UI (EN/RU/BG)
- Free-tier monthly audit limits

## What needs keys

| Integration | Env vars |
|-------------|----------|
| Live AI audit | `ROUTERAI_API_KEY` or `OPENROUTER_API_KEY` |
| Stripe checkout | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` |
| YooKassa | `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` |
| YouTube Data API | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |

## Install

```bash
cp .env.example .env
# set APP_SECRET_KEY, POSTGRES_PASSWORD, optional AI keys
bash scripts/go_live.sh
```

Tag:

```bash
git tag -a v0.1.0-beta -m "VRAV Tube Engine commercial beta"
git push origin v0.1.0-beta
```

## Not claimed

- Guaranteed YouTube ranking or monetization outcomes
- Affiliation with YouTube/Google
- Full payment certification without merchant accounts

## Support

Enterprise / white-label: use the contact form on the landing page (`POST /api/v1/contact`).
