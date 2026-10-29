# AI Providers

## Configured adapters

| Provider | Base URL | Config keys | Status |
|----------|----------|-------------|--------|
| RouterAI | `https://routerai.ru/api/v1` | `ROUTERAI_API_KEY`, `ROUTERAI_BASE_URL`, `ROUTERAI_DEFAULT_MODEL` | Primary for RU market |
| OpenRouter | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_DEFAULT_MODEL` | International |
| xAI / Grok | `https://api.x.ai/v1` | `XAI_API_KEY` | Optional |

All three use the OpenAI-compatible Chat Completions protocol via `OpenAICompatibleProvider`.

## Routing

`AIGateway.preferred_order()` prefers RouterAI when configured, then OpenRouter, then xAI.  
Failures fall through to the next provider.  
If **no** keys are set, the audit pipeline runs in **offline structural mode** (no fabricated SEO metrics).

## Cost tracking

`ai_usage_records` table stores provider, model, tokens, costs and outcome per tenant.

## Security

- API keys are server-side only.
- Transcripts and metadata are treated as untrusted (prompt-injection aware system prompt).
- AI output is JSON-schema validated before persistence.
