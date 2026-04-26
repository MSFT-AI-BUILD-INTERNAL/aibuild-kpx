"""Per-model token-usage benchmark.

For each (prompt × variant × model_family), measure:
- prompt_tokens (model's own tokenizer when available)
- savings_pct vs raw V0
- estimated USD cost (prompt-side only)
- absolute token delta

Tokenizer accuracy:
- OpenAI (gpt-4o*, gpt-5*): exact via ``tiktoken`` (o200k_base)
- Anthropic (claude-*): heuristic. Anthropic public guidance "1 token ≈ 3.5 chars"
  for English; we use that ratio (CJK 1 char = 1 token, ASCII 3.5 chars/tok).
- Google (gemini-*): heuristic. Public docs ~4 chars/token (SentencePiece);
  we use 4 chars/token for ASCII, 1 char/token for CJK.

Heuristics are clearly labeled in the JSON output as ``tokenizer_kind``.

Pricing (2026 Q1 public list, USD per 1M input tokens) is intentionally
configurable in ``MODEL_PRICING`` so users can override without code changes.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable, Optional
import json
import os

from kpx import compress
from bench_real.analysis.realistic_prompts import CORPUS, CodePrompt


# ---------- tokenizer backends ----------

try:
    import tiktoken  # type: ignore
    _TIK = tiktoken.get_encoding("o200k_base")
except Exception:
    _TIK = None


def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (
        0x3040 <= o <= 0x30FF or  # Japanese kana
        0x3400 <= o <= 0x9FFF or  # CJK
        0xAC00 <= o <= 0xD7AF or  # Hangul
        0xF900 <= o <= 0xFAFF
    )


def _ratio_count(text: str, ascii_chars_per_tok: float) -> int:
    cjk = sum(1 for c in text if _is_cjk(c))
    other = len(text) - cjk
    return cjk + max(1, round(other / ascii_chars_per_tok))


def count_openai(text: str) -> int:
    if _TIK is not None:
        return len(_TIK.encode(text))
    return _ratio_count(text, 4.0)


def count_anthropic(text: str) -> int:
    return _ratio_count(text, 3.5)


def count_gemini(text: str) -> int:
    return _ratio_count(text, 4.0)


@dataclass(frozen=True)
class ModelSpec:
    family: str
    model: str
    counter: Callable[[str], int]
    tokenizer_kind: str        # "exact" | "heuristic"
    usd_per_1m_input: float    # 2026-04 list price


MODELS: list[ModelSpec] = [
    # OpenAI
    ModelSpec("openai", "gpt-4o-mini", count_openai, "exact", 0.15),
    ModelSpec("openai", "gpt-4o",      count_openai, "exact", 2.50),
    ModelSpec("openai", "gpt-5-mini",  count_openai, "exact", 0.25),
    ModelSpec("openai", "gpt-5.4",     count_openai, "exact", 5.00),
    # Anthropic
    ModelSpec("anthropic", "claude-haiku-4.5",  count_anthropic, "heuristic", 1.00),
    ModelSpec("anthropic", "claude-sonnet-4.7", count_anthropic, "heuristic", 3.00),
    ModelSpec("anthropic", "claude-opus-4.7",   count_anthropic, "heuristic", 15.00),
    # Google
    ModelSpec("google", "gemini-1.5-flash", count_gemini, "heuristic", 0.075),
    ModelSpec("google", "gemini-1.5-pro",   count_gemini, "heuristic", 1.25),
    ModelSpec("google", "gemini-2.5-pro",   count_gemini, "heuristic", 2.50),
]


# ---------- variants ----------

VARIANT_METHODS = {
    "V0_raw":      None,                         # no transform
    "V3_safe3":    ["M03", "M24", "M25"],
    "V4_all_safe": ["M03", "M04", "M19", "M24", "M25"],
}


def _apply_variant(text: str, methods: Optional[list[str]]) -> str:
    if methods is None:
        return text
    return compress(text, methods=methods)


# ---------- main ----------

@dataclass
class Cell:
    prompt_id: str
    label: str
    lang: str
    family: str
    model: str
    variant: str
    tokenizer_kind: str
    tokens: int
    tokens_v0: int
    savings_pct: float
    usd_per_call: float        # prompt-side only, for ONE call
    usd_per_1k_calls: float


def _round(x: float, n: int = 4) -> float:
    return round(x, n)


def run() -> dict:
    cells: list[Cell] = []
    # cache V0 tokens per (prompt, model) so savings are consistent
    v0_tokens: dict[tuple[str, str], int] = {}

    for p in CORPUS:
        for ms in MODELS:
            for variant_name, methods in VARIANT_METHODS.items():
                text = _apply_variant(p.text, methods)
                t = ms.counter(text)
                if variant_name == "V0_raw":
                    v0_tokens[(p.id, ms.model)] = t
                t0 = v0_tokens.get((p.id, ms.model), t)
                save = 0.0 if t0 == 0 else round((t0 - t) / t0 * 100.0, 2)
                usd = round(t * ms.usd_per_1m_input / 1_000_000.0, 6)
                cells.append(Cell(
                    prompt_id=p.id,
                    label=p.label,
                    lang=p.lang,
                    family=ms.family,
                    model=ms.model,
                    variant=variant_name,
                    tokenizer_kind=ms.tokenizer_kind,
                    tokens=t,
                    tokens_v0=t0,
                    savings_pct=save,
                    usd_per_call=usd,
                    usd_per_1k_calls=round(usd * 1000, 4),
                ))

    # ---- aggregations ----
    by_model_variant: dict[str, dict[str, dict]] = {}
    for c in cells:
        d = by_model_variant.setdefault(c.model, {}).setdefault(c.variant, {
            "n": 0, "sum_tokens": 0, "sum_v0": 0,
            "sum_usd": 0.0, "savings_list": [],
        })
        d["n"] += 1
        d["sum_tokens"] += c.tokens
        d["sum_v0"] += c.tokens_v0
        d["sum_usd"] += c.usd_per_call
        d["savings_list"].append(c.savings_pct)
    summary_model: list[dict] = []
    for model, vs in by_model_variant.items():
        for variant, d in vs.items():
            sl = d["savings_list"]
            v0 = d["sum_v0"] or 1
            summary_model.append({
                "model": model,
                "variant": variant,
                "n": d["n"],
                "tokens_total": d["sum_tokens"],
                "tokens_v0_total": d["sum_v0"],
                "tokens_saved_total": d["sum_v0"] - d["sum_tokens"],
                "savings_pct_avg": _round(sum(sl) / len(sl), 2),
                "savings_pct_corpus": _round(
                    (d["sum_v0"] - d["sum_tokens"]) / v0 * 100.0, 2),
                "usd_total_15_prompts": _round(d["sum_usd"], 6),
                "usd_per_1k_prompts": _round(d["sum_usd"] * 1000 / d["n"], 4),
            })

    # variant-only roll-up across all models (corpus-weighted)
    by_variant: dict[str, dict] = {}
    for c in cells:
        d = by_variant.setdefault(c.variant, {
            "sum_tokens": 0, "sum_v0": 0, "savings_list": [],
        })
        d["sum_tokens"] += c.tokens
        d["sum_v0"] += c.tokens_v0
        d["savings_list"].append(c.savings_pct)
    summary_variant: list[dict] = []
    for v, d in by_variant.items():
        sl = d["savings_list"]
        v0 = d["sum_v0"] or 1
        summary_variant.append({
            "variant": v,
            "n_cells": len(sl),
            "savings_pct_avg": _round(sum(sl) / len(sl), 2),
            "savings_pct_corpus": _round(
                (d["sum_v0"] - d["sum_tokens"]) / v0 * 100.0, 2),
        })

    # cost @ scale: 1M user requests/month at V0 vs V4
    cost_at_scale: list[dict] = []
    for ms in MODELS:
        v0 = sum(c.tokens for c in cells
                 if c.model == ms.model and c.variant == "V0_raw")
        v4 = sum(c.tokens for c in cells
                 if c.model == ms.model and c.variant == "V4_all_safe")
        n = sum(1 for c in cells
                if c.model == ms.model and c.variant == "V0_raw")
        if n == 0:
            continue
        avg_v0 = v0 / n
        avg_v4 = v4 / n
        # 1M calls/month
        usd_v0 = avg_v0 * ms.usd_per_1m_input  # (avg tokens) * ($/1M) * 1M calls / 1M
        usd_v4 = avg_v4 * ms.usd_per_1m_input
        cost_at_scale.append({
            "family": ms.family,
            "model": ms.model,
            "avg_prompt_tokens_v0": _round(avg_v0, 1),
            "avg_prompt_tokens_v4": _round(avg_v4, 1),
            "usd_per_1M_calls_v0": _round(usd_v0, 2),
            "usd_per_1M_calls_v4": _round(usd_v4, 2),
            "monthly_savings_usd": _round(usd_v0 - usd_v4, 2),
            "monthly_savings_pct": _round(
                (usd_v0 - usd_v4) / usd_v0 * 100.0, 2) if usd_v0 else 0.0,
        })

    return {
        "meta": {
            "n_prompts": len(CORPUS),
            "n_models": len(MODELS),
            "n_variants": len(VARIANT_METHODS),
            "n_cells": len(cells),
            "tiktoken_available": _TIK is not None,
            "pricing_date": "2026-04",
            "pricing_unit": "USD per 1M input tokens (list price)",
            "tokenizer_notes": {
                "openai": "exact via tiktoken o200k_base"
                          if _TIK else "fallback ratio 4 chars/token",
                "anthropic": "heuristic 3.5 chars/token (ASCII), 1 char/token CJK",
                "google":    "heuristic 4 chars/token (ASCII), 1 char/token CJK",
            },
        },
        "cells": [asdict(c) for c in cells],
        "summary_by_model_variant": summary_model,
        "summary_by_variant": summary_variant,
        "cost_at_scale_1M_calls": cost_at_scale,
    }


def write(path: str = "bench_real/model_compare/results/model_compare.json") -> dict:
    out = run()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    return out
