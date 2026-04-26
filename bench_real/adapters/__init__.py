"""LLM adapter interface + factory.

All adapters return a uniform CallResult so the runner is provider-agnostic.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class CallResult:
    text: str
    prompt_tokens: int          # API-reported, fallback to 0
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    model: str
    error: Optional[str] = None
    raw: Optional[dict] = None  # for debugging


class Adapter:
    name: str = "abstract"
    model: str = "unknown"

    def call(self, system: str, user: str, *, max_tokens: int = 1024,
             temperature: float = 0.0) -> CallResult:
        raise NotImplementedError


def get_adapter(name: str, model: str | None = None) -> Adapter:
    """Return an Adapter for the given provider name."""
    name = name.lower()
    if name == "mock":
        from .mock import MockAdapter
        return MockAdapter(model=model or "mock")
    if name == "openai":
        from .openai import OpenAIAdapter
        return OpenAIAdapter(model=model or "gpt-4o-mini")
    if name == "anthropic":
        from .anthropic import AnthropicAdapter
        return AnthropicAdapter(model=model or "claude-sonnet-4.7")
    if name in ("google", "gemini"):
        from .google import GoogleAdapter
        return GoogleAdapter(model=model or "gemini-1.5-flash")
    raise ValueError(f"unknown adapter: {name}")
