"""Google Gemini adapter via REST (urllib-only, no SDK dep).

Uses the public ``generativelanguage.googleapis.com`` v1beta endpoint:
``POST /v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}``.
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error

from . import Adapter, CallResult


class GoogleAdapter(Adapter):
    name = "google"
    base = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model: str = "gemini-1.5-flash",
                 api_key: str | None = None):
        self.model = model
        self.api_key = (
            api_key
            or os.environ.get("GOOGLE_API_KEY", "")
            or os.environ.get("GEMINI_API_KEY", "")
        )

    def call(self, system: str, user: str, *, max_tokens: int = 1024,
             temperature: float = 0.0) -> CallResult:
        if not self.api_key:
            return CallResult("", 0, 0, 0, 0, self.model,
                              error="GOOGLE_API_KEY / GEMINI_API_KEY not set")
        url = f"{self.base}/{self.model}:generateContent?key={self.api_key}"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
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
            cand = (data.get("candidates") or [{}])[0]
            parts = ((cand.get("content") or {}).get("parts")) or []
            text = "".join(p.get("text", "") for p in parts)
            usage = data.get("usageMetadata", {})
            p = int(usage.get("promptTokenCount", 0))
            c = int(usage.get("candidatesTokenCount", 0))
            t = int(usage.get("totalTokenCount", p + c))
        except Exception as e:
            return CallResult("", 0, 0, 0, latency, self.model,
                              error=f"bad response shape: {e}", raw=data)
        return CallResult(text, p, c, t, latency, self.model, raw=data)
