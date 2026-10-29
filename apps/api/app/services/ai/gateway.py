"""AI Gateway — routes tasks to configured providers with fallback."""

from typing import Any, Optional

from app.core.config import get_settings
from app.services.ai.base import AIProvider, ChatMessage, ChatResponse
from app.services.ai.openai_compatible import OpenAICompatibleProvider


def _build_providers() -> dict[str, AIProvider]:
    settings = get_settings()
    providers: dict[str, AIProvider] = {}

    if settings.openrouter_api_key:
        providers["openrouter"] = OpenAICompatibleProvider(
            name="openrouter",
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            default_model=settings.openrouter_default_model,
            timeout=float(settings.ai_timeout_seconds),
            extra_headers={
                "HTTP-Referer": settings.app_base_url,
                "X-Title": "VRAV Tube Engine",
            },
        )

    if settings.routerai_api_key and settings.feature_routerai:
        providers["routerai"] = OpenAICompatibleProvider(
            name="routerai",
            api_key=settings.routerai_api_key,
            base_url=settings.routerai_base_url,
            default_model=settings.routerai_default_model,
            timeout=float(settings.ai_timeout_seconds),
        )

    if settings.xai_api_key:
        providers["xai"] = OpenAICompatibleProvider(
            name="xai",
            api_key=settings.xai_api_key,
            base_url=settings.xai_base_url,
            default_model="grok-2-latest",
            timeout=float(settings.ai_timeout_seconds),
        )

    return providers


class AIGateway:
    """Task-aware routing with ordered fallback."""

    def __init__(self) -> None:
        self._providers = _build_providers()

    @property
    def available_providers(self) -> list[str]:
        return list(self._providers.keys())

    def get_provider(self, name: str) -> AIProvider:
        if name not in self._providers:
            raise RuntimeError(
                f"Provider '{name}' is not configured. "
                f"Available: {self.available_providers or 'none'}"
            )
        return self._providers[name]

    def preferred_order(self, task: str = "general") -> list[str]:
        order = []
        if "routerai" in self._providers:
            order.append("routerai")
        if "openrouter" in self._providers:
            order.append("openrouter")
        if "xai" in self._providers:
            order.append("xai")
        return order

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        task: str = "general",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict[str, Any]] = None,
    ) -> ChatResponse:
        if not self._providers:
            raise RuntimeError(
                "No AI providers configured. Set ROUTERAI_API_KEY and/or OPENROUTER_API_KEY."
            )

        if provider:
            candidates = [provider]
        else:
            candidates = self.preferred_order(task)

        last_error: Optional[Exception] = None
        for name in candidates:
            if name not in self._providers:
                continue
            try:
                p = self._providers[name]
                return await p.chat_completion(
                    messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except Exception as exc:
                last_error = exc
                continue

        raise RuntimeError(
            f"All AI providers failed. Last error: {last_error}"
        ) from last_error


_gateway: Optional[AIGateway] = None


def get_ai_gateway() -> AIGateway:
    global _gateway
    if _gateway is None:
        _gateway = AIGateway()
    return _gateway
