"""Anthropic Messages API adapter (urllib-only)."""
from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error

from . import Adapter, CallResult


class AnthropicAdapter(Adapter):
    name = "anthropic"
    endpoint = "https://api.anthropic.com/v1/messages"
    api_version = "2023-06-01"

    def __init__(self, model: str = "claude-sonnet-4.7",
                 api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def call(self, system: str, user: str, *, max_tokens: int = 1024,
             temperature: float = 0.0) -> CallResult:
        if not self.api_key:
            return CallResult("", 0, 0, 0, 0, self.model,
                              error="ANTHROPIC_API_KEY not set")
        body = {
            "model": self.model,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": self.api_version,
            },
            method="POST",
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return CallResult("", 0, 0, 0, int((time.time()-t0)*1000),
                              self.model, error=f"HTTP {e.code}: {e.read()[:200]!r}")
        except Exception as e:
            return CallResult("", 0, 0, 0, int((time.time()-t0)*1000),
                              self.model, error=f"{type(e).__name__}: {e}")
        latency = int((time.time() - t0) * 1000)
        try:
            blocks = data.get("content", [])
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            usage = data.get("usage", {})
            p = int(usage.get("input_tokens", 0))
            c = int(usage.get("output_tokens", 0))
        except Exception as e:
            return CallResult("", 0, 0, 0, latency, self.model,
                              error=f"bad response shape: {e}", raw=data)
        return CallResult(text, p, c, p + c, latency, self.model, raw=data)
