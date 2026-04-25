"""Tier-2 LLM-as-judge. 4 axes × 25 = 100. Cross-vendor by design."""
from __future__ import annotations
import json
import re
from pathlib import Path

from ..adapters import Adapter


_DEFAULT_PROMPT = (Path(__file__).resolve().parent.parent / "judge_prompt.md").read_text(
    encoding="utf-8", errors="replace"
) if (Path(__file__).resolve().parent.parent / "judge_prompt.md").exists() else ""


def score_llm_judge(judge: Adapter, *, system: str, user: str,
                    response: str, prompt_template: str | None = None,
                    ) -> tuple[float, dict]:
    """Return (score 0..100, axes_dict)."""
    template = prompt_template or _DEFAULT_PROMPT
    prompt = (
        template
        .replace("{{SYSTEM}}", system)
        .replace("{{USER}}", user)
        .replace("{{RESPONSE}}", response)
    )
    res = judge.call(system="You are a strict, calibrated grader.", user=prompt,
                     max_tokens=400, temperature=0.0)
    if res.error:
        return (0.0, {"error": res.error})
    text = res.text
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return (0.0, {"error": "no json", "raw": text[:200]})
    try:
        data = json.loads(m.group(0))
    except Exception as e:
        return (0.0, {"error": f"parse: {e}", "raw": text[:200]})
    axes = ("correctness", "completeness", "faithfulness", "conciseness")
    parts = []
    for a in axes:
        v = data.get(a, 0)
        try:
            parts.append(max(0, min(25, int(v))))
        except (TypeError, ValueError):
            parts.append(0)
    return (float(sum(parts)), {a: p for a, p in zip(axes, parts)})
