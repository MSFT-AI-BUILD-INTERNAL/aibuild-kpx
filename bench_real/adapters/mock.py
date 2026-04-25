"""Deterministic mock adapter.

Used when API keys are unavailable. Produces task-shaped responses so
rule-based scorers exercise their full code paths. Token counts mirror the
kpx heuristic so the pipeline behaves identically to a real provider for
non-quality assertions.
"""
from __future__ import annotations
import hashlib
import random
import re
import time

from kpx.tokens import estimate_tokens
from . import Adapter, CallResult


_REFUSE_KEYWORDS = (
    "how to make a bomb", "child sexual", "ddos", "self-harm",
    "synthesize a virus", "malware", "credit card numbers",
    "bypass authentication", "stalk", "doxx",
)


def _seeded_choice(seq, key: str):
    h = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    return seq[h % len(seq)]


class MockAdapter(Adapter):
    name = "mock"

    def __init__(self, model: str = "mock"):
        self.model = model

    def call(self, system: str, user: str, *, max_tokens: int = 1024,
             temperature: float = 0.0) -> CallResult:
        t0 = time.time()
        text = self._respond(system, user)
        latency = int((time.time() - t0) * 1000) + 1
        p_tok = estimate_tokens(system) + estimate_tokens(user)
        c_tok = estimate_tokens(text)
        return CallResult(
            text=text, prompt_tokens=p_tok, completion_tokens=c_tok,
            total_tokens=p_tok + c_tok, latency_ms=latency, model=self.model,
        )

    # -- response heuristics, branching on user-message shape ----------------
    def _respond(self, system: str, user: str) -> str:
        u_low = user.lower()

        # safety refusal
        if any(k in u_low for k in _REFUSE_KEYWORDS):
            return ("I can't help with that request. If you're in distress, "
                    "consider contacting a qualified professional.")

        # JSON extraction
        if "json" in u_low and "extract" in u_low:
            return self._mock_json(user)

        # tool selection
        if "available tools" in u_low or "choose the best tool" in u_low:
            return self._mock_tool(user)

        # translation
        if "translate" in u_low:
            return self._mock_translation(user)

        # summary
        if "summarize" in u_low or "요약" in user:
            return self._mock_summary(user)

        # python coding
        if "python" in u_low or "def " in user or "function" in u_low:
            return self._mock_code(user)

        # default short answer
        return "OK."

    def _mock_code(self, user: str) -> str:
        m = re.search(r"def\s+(\w+)\s*\(([^)]*)\)", user)
        if not m:
            return "```python\ndef solve():\n    return None\n```"
        name, params = m.group(1), m.group(2)
        param_names = [p.strip().split(":")[0] for p in params.split(",") if p.strip()]
        # task-specific stubs by function name
        body = {
            "add": "    return a + b",
            "is_even": "    return n % 2 == 0",
            "reverse_string": "    return s[::-1]",
            "factorial": "    r = 1\n    for i in range(1, n+1):\n        r *= i\n    return r",
            "sum_list": "    return sum(xs)",
            "count_vowels": "    return sum(1 for c in s.lower() if c in 'aeiou')",
            "is_palindrome": "    s = s.lower()\n    return s == s[::-1]",
            "fizzbuzz": ("    out = []\n    for i in range(1, n+1):\n"
                          "        if i%15==0: out.append('FizzBuzz')\n"
                          "        elif i%3==0: out.append('Fizz')\n"
                          "        elif i%5==0: out.append('Buzz')\n"
                          "        else: out.append(str(i))\n    return out"),
            "max_of": "    return max(xs)",
            "unique": "    seen = []\n    for x in xs:\n        if x not in seen: seen.append(x)\n    return seen",
        }.get(name, f"    return {param_names[0] if param_names else 'None'}")
        return f"```python\ndef {name}({params}):\n{body}\n```"

    def _mock_json(self, user: str) -> str:
        # echo back any "name: ... age: ..." style fields
        kv = dict(re.findall(r"(\w+)\s*[:=]\s*\"?([^,\"\n]+)\"?", user))
        # drop noisy keys
        for noisy in ("type", "extract", "schema", "json", "from", "the", "task"):
            kv.pop(noisy, None)
        if not kv:
            kv = {"value": "unknown"}
        import json
        return "```json\n" + json.dumps(kv, ensure_ascii=False) + "\n```"

    def _mock_tool(self, user: str) -> str:
        m = re.search(r"tools?:\s*\[([^\]]+)\]", user, re.I)
        tools = []
        if m:
            tools = [t.strip().strip("'\"") for t in m.group(1).split(",")]
        if not tools:
            return "search"
        # heuristic mapping
        if "weather" in user.lower():
            for t in tools:
                if "weather" in t.lower():
                    return t
        if "search" in user.lower() or "find" in user.lower():
            for t in tools:
                if "search" in t.lower():
                    return t
        if "calculate" in user.lower() or "compute" in user.lower():
            for t in tools:
                if "calc" in t.lower() or "math" in t.lower():
                    return t
        return _seeded_choice(tools, user)

    def _mock_translation(self, user: str) -> str:
        # extract quoted phrase
        m = re.search(r'"([^"]+)"', user) or re.search(r"`([^`]+)`", user)
        src = m.group(1) if m else user.split(":")[-1].strip()
        # naive direction detection
        if any("\uac00" <= c <= "\ud7af" for c in src):
            return f'"Translation of: {src}"'
        return f'"{src}의 번역"'

    def _mock_summary(self, user: str) -> str:
        # take first sentence + first bullet-ish thing
        sents = re.split(r"(?<=[.!?])\s+|\n\n", user)
        head = sents[0] if sents else user[:100]
        return f"Summary: {head[:200]}"
