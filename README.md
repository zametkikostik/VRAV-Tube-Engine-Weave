# VRAV Tube Engine

**AI YouTube Audit, SEO & Monetization Risk Platform**

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](apps/api)
[![React](https://img.shields.io/badge/react-19-61dafb.svg)](apps/web)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688.svg)](apps/api)

Proprietary commercial SaaS / White-Label / Self-Hosted software for YouTube creators, production studios, marketing agencies and channel managers.

> **Not affiliated with YouTube or Google.** Reports are advisory only — no guaranteed rankings, monetization or revenue.

---

## About

VRAV Tube Engine helps teams answer:

- What should change before publishing?
- Are title and description clear and aligned with content?
- Which SEO improvements are worth reviewing?
- Are there potential policy / monetization risk signals?
- How can agencies deliver branded audit reports?

**Languages:** English · Русский · Български  

**Deploy:** Linux VDS · Windows (Docker) · Linux desktop · Android PWA  

**AI:** [RouterAI](https://routerai.ru) · OpenRouter · optional xAI/Grok  

**Payments:** Stripe · YooKassa (when eligible)

---

## Topics / tags

`youtube` `seo` `ai` `fastapi` `react` `saas` `white-label` `monetization` `audit` `pwa` `typescript` `postgresql` `celery` `multilingual` `bulgaria` `russia`

---

## Quick start

```bash
cp .env.example .env
# optional: ROUTERAI_API_KEY, STRIPE_*, GOOGLE_CLIENT_*

docker compose up -d --build
docker compose exec api alembic upgrade head

# Frontend
cd apps/web && npm install && npm run dev

# API docs
open http://localhost:8000/docs
```

E2E smoke (API must be up):

```bash
./scripts/e2e_smoke.sh http://localhost:8000/api/v1
```

---

## Status

See [docs/PHASE_STATUS.md](docs/PHASE_STATUS.md) and [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md).

| Area | Status |
|------|--------|
| Auth, tenants, i18n | Done |
| Video intake + audit pipeline | Done (offline + AI) |
| HTML/PDF reports | Done |
| AI gateway (RouterAI/OpenRouter) | Done |
| Stripe/YooKassa adapters + webhooks | Done (needs keys) |
| YouTube OAuth + Data API | Done (needs Google Cloud) |
| White-label API | Done |
| Entitlements / quotas | Done |
| FFmpeg sampling helper | Done |

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design |
| [DATA_MODEL.md](docs/DATA_MODEL.md) | Schema |
| [AI_PROVIDERS.md](docs/AI_PROVIDERS.md) | AI routing |
| [YOUTUBE_INTEGRATION.md](docs/YOUTUBE_INTEGRATION.md) | OAuth + Data API |
| [PAYMENTS.md](docs/PAYMENTS.md) | Stripe / YooKassa |
| [SANDBOX_KEYS.md](docs/SANDBOX_KEYS.md) | How to obtain test keys |
| [DEPLOYMENT_VDS.md](docs/DEPLOYMENT_VDS.md) | Production VDS |
| [ANDROID_PWA.md](docs/ANDROID_PWA.md) | Mobile PWA |
| [PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) | Checklist |
| [RELEASING.md](docs/RELEASING.md) | GitHub Releases |

---

## GitHub Releases

Creating a release (or pushing a `v*` tag) triggers **Release** workflow which attaches:

| Asset | Contents |
|-------|----------|
| `*-source.tar.gz` | Full source snapshot |
| `*-web-dist.zip` | Built SPA (`apps/web/dist`) |
| `*-deploy-bundle.zip` | Compose, Nginx/Caddy, scripts, key docs |
| `SHA256SUMS-*.txt` | Checksums |

```bash
git tag -a v0.1.0-beta -m "VRAV Tube Engine commercial beta"
git push origin main
git push origin v0.1.0-beta
# Or: GitHub → Releases → Draft a new release → Publish
```

---

## License

**Proprietary commercial.** See [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md).

Unauthorized production use or redistribution is prohibited.

---

## Repository

https://github.com/zametkikostik/VRAV-Tube-Engine-Weave
