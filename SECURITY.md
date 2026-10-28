# Security

## Reporting

Report security issues privately to the maintainers. Do not open public issues for vulnerabilities.

## Practices

- Secrets only in environment variables / secret managers
- Passwords hashed with Argon2
- JWT access + refresh tokens
- Tenant isolation enforced server-side on every object access
- AI provider keys never shipped to the browser
- Payment webhooks cryptographically verified before entitlements
- Rate limiting and security headers on the API
- Upload and media processing path constraints

## Disclosures

This product is not affiliated with YouTube or Google.
Audit reports are advisory and do not guarantee monetization or ranking outcomes.
