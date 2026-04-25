"""OpenAI Chat Completions adapter (urllib-only, no SDK dep)."""
from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error

from . import Adapter, CallResult


class OpenAIAdapter(Adapter):
    name = "openai"
    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self, model: str = "gpt-4o-mini",
                 api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def call(self, system: str, user: str, *, max_tokens: int = 1024,
             temperature: float = 0.0) -> CallResult:
        if not self.api_key:
            return CallResult("", 0, 0, 0, 0, self.model,
                              error="OPENAI_API_KEY not set")
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
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
            text = data["choices"][0]["message"]["content"] or ""
            usage = data.get("usage", {})
            p = int(usage.get("prompt_tokens", 0))
            c = int(usage.get("completion_tokens", 0))
            t = int(usage.get("total_tokens", p + c))
        except (KeyError, IndexError, TypeError) as e:
            return CallResult("", 0, 0, 0, latency, self.model,
                              error=f"bad response shape: {e}", raw=data)
        return CallResult(text, p, c, t, latency, self.model, raw=data)
