"""OpenAI-compatible chat completions client (OpenRouter, RouterAI, etc.)."""

from typing import Any, Optional

import httpx

from app.services.ai.base import AIProvider, ChatMessage, ChatResponse, UsageInfo


class OpenAICompatibleProvider(AIProvider):
    def __init__(
        self,
        *,
        name: str,
        api_key: str,
        base_url: str,
        default_model: str = "",
        timeout: float = 120.0,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self.extra_headers = extra_headers or {}

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        *,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> ChatResponse:
        if not self.api_key:
            raise RuntimeError(f"{self.name}: API key is not configured")

        use_model = model or self.default_model
        if not use_model:
            raise RuntimeError(f"{self.name}: no model specified and no default configured")

        payload: dict[str, Any] = {
            "model": use_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code == 401:
                raise RuntimeError(f"{self.name}: authentication failed (check API key)")
            if resp.status_code == 429:
                raise RuntimeError(f"{self.name}: rate limit exceeded")
            if resp.status_code >= 400:
                detail = resp.text[:500]
                raise RuntimeError(f"{self.name}: HTTP {resp.status_code}: {detail}")

            data = resp.json()

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        usage_raw = data.get("usage") or {}
        usage = UsageInfo(
            prompt_tokens=int(usage_raw.get("prompt_tokens") or 0),
            completion_tokens=int(usage_raw.get("completion_tokens") or 0),
            total_tokens=int(usage_raw.get("total_tokens") or 0),
        )

        return ChatResponse(
            content=content,
            model=data.get("model") or use_model,
            provider=self.name,
            usage=usage,
            raw=data,
            finish_reason=choice.get("finish_reason"),
        )

    async def list_models(self) -> list[dict[str, Any]]:
        if not self.api_key:
            return []
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.base_url}/models",
                headers=self._headers(),
            )
            if resp.status_code >= 400:
                return []
            data = resp.json()
            return data.get("data") or data.get("models") or []
