"""GitHub Models API adapter (OpenAI-compatible).

Uses ``gh auth token`` (or GITHUB_TOKEN env) — no third-party API key required.
Endpoint: https://models.github.ai/inference/chat/completions
"""
from __future__ import annotations
import json
import os
import subprocess
import time
import urllib.request
import urllib.error

from . import Adapter, CallResult


_REASONING_PREFIXES = ("openai/o1", "openai/o3", "openai/o4",
                       "microsoft/phi-4-reasoning",
                       "microsoft/phi-4-mini-reasoning",
                       "microsoft/mai-ds-r1",
                       "deepseek/deepseek-r1")


def _resolve_token() -> str:
    tok = os.environ.get("GITHUB_MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok
    try:
        out = subprocess.run(["gh", "auth", "token"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return ""


class GithubModelsAdapter(Adapter):
    name = "github"
    endpoint = "https://models.github.ai/inference/chat/completions"

    def __init__(self, model: str = "openai/gpt-4o-mini",
                 token: str | None = None):
        self.model = model
        self.token = token or _resolve_token()
        self._is_reasoning = any(model.startswith(p) for p in _REASONING_PREFIXES)

    def call(self, system: str, user: str, *, max_tokens: int = 1024,
             temperature: float = 0.0) -> CallResult:
        if not self.token:
            return CallResult("", 0, 0, 0, 0, self.model,
                              error="no GitHub token (gh auth token failed)")

        # Reasoning models on GitHub Models require special handling:
        # - no `system` role (fold into user)
        # - no `temperature` param
        # - use `max_completion_tokens` instead of `max_tokens`
        if self._is_reasoning:
            messages = [{"role": "user",
                         "content": f"{system}\n\n---\n\n{user}"}]
            body: dict = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": max_tokens,
            }
        else:
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
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            },
            method="POST",
        )
        t0 = time.time()
        # Retry loop for transient errors (429 rate limit, 5xx).
        # Hard cap on cumulative backoff to avoid wedging a benchmark on a
        # persistently throttled model (see rounds/round-8 — judge model was
        # permanently 429 and previous policy retried for >1200s).
        MAX_TOTAL_WAIT_S = 60.0
        total_wait = 0.0
        attempt = 0
        while True:
            attempt += 1
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                body_snip = e.read()[:300]
                retryable = e.code == 429 or 500 <= e.code < 600
                if retryable and attempt <= 4 and total_wait < MAX_TOTAL_WAIT_S:
                    # Respect Retry-After if present, else exp backoff.
                    ra = e.headers.get("retry-after") if e.headers else None
                    try:
                        wait = float(ra) if ra else min(30.0, 2 ** attempt)
                    except ValueError:
                        wait = min(30.0, 2 ** attempt)
                    # Clip so cumulative does not exceed MAX_TOTAL_WAIT_S.
                    wait = min(wait, max(0.0, MAX_TOTAL_WAIT_S - total_wait))
                    total_wait += wait
                    time.sleep(wait)
                    continue
                return CallResult("", 0, 0, 0, int((time.time()-t0)*1000),
                                  self.model,
                                  error=f"HTTP {e.code}: {body_snip!r}")
            except Exception as e:
                if attempt <= 2:
                    time.sleep(2 ** attempt)
                    continue
                return CallResult("", 0, 0, 0, int((time.time()-t0)*1000),
                                  self.model, error=f"{type(e).__name__}: {e}")
        latency = int((time.time() - t0) * 1000)
        try:
            text = data["choices"][0]["message"].get("content") or ""
            usage = data.get("usage", {})
            p = int(usage.get("prompt_tokens", 0))
            c = int(usage.get("completion_tokens", 0))
            tt = int(usage.get("total_tokens", p + c))
        except (KeyError, IndexError, TypeError) as e:
            return CallResult("", 0, 0, 0, latency, self.model,
                              error=f"bad response shape: {e}", raw=data)
        return CallResult(text, p, c, tt, latency, self.model, raw=data)
