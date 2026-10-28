"""Unified AI provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class UsageInfo:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    provider_reported_cost: Optional[float] = None
    currency: str = "USD"


@dataclass
class ChatResponse:
    content: str
    model: str
    provider: str
    usage: UsageInfo = field(default_factory=UsageInfo)
    raw: Optional[dict[str, Any]] = None
    finish_reason: Optional[str] = None


class AIProvider(ABC):
    """Abstract AI provider. All adapters implement this."""

    name: str

    @abstractmethod
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
        ...

    @abstractmethod
    async def list_models(self) -> list[dict[str, Any]]:
        ...

    async def health_check(self) -> bool:
        try:
            models = await self.list_models()
            return len(models) >= 0
        except Exception:
            return False
