# Changelog

## [0.1.0-beta] — 2026-10-28

### Added
- Multi-tenant FastAPI API: auth, organizations, tenants, projects, videos, audits
- Offline structural audit + AI gateway (RouterAI, OpenRouter, xAI)
- HTML and PDF report export
- Stripe / YooKassa adapters with verified webhook processing and subscription activation
- YouTube OAuth + Data API metadata fetch (tokens in DB)
- White-label settings API
- Entitlements / monthly audit quotas
- Billing UI and landing pricing (EN/RU/BG)
- Enterprise contact form + admin panel (superuser)
- FFmpeg frame sampling helper
- Docker Compose (dev + prod), Nginx/Caddy configs
- CI: unit tests + e2e smoke against Postgres
- Go-live and e2e scripts
- GitHub Release workflow (source, web-dist, deploy-bundle, checksums)

### Security
- Argon2 passwords, JWT access/refresh
- Rate limiting, security headers
- Server-side AI keys only
- Webhook entitlements only when verified=True

### Known limitations
- Live payment / YouTube / AI require operator keys
- RLS not enabled; isolation is application-level
- YooKassa production verification must follow official IP/signature rules
- FFmpeg not fully wired into default audit stages
