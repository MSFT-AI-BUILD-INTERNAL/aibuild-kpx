"""Static, API-free analysis of kpx's effect on source-code prompts.

Measures, per (prompt × variant):
  - tokens before/after (kpx heuristic)
  - chars before/after
  - **byte-exact code-block preservation** — every \\`\\`\\`fenced block in V0
    must appear verbatim in the variant output (kpx invariant)
  - **inline identifier preservation** — every \\`identifier\\` in V0 must
    appear in the variant output
  - **signpost preservation** — technical signposts ("Please note", "step
    by step", etc.) survive
  - **politeness removal** — politeness filler is actually gone
  - **AST stability for embedded Python** — any python code block parses
    to identical ast.dump in V0 and the variant
  - **idempotency** — applying the variant twice == once

Output: a structured dict suitable for JSON dump and HTML rendering.
"""
from __future__ import annotations
import ast
import re
from dataclasses import dataclass, asdict
from typing import Iterable

from kpx.tokens import estimate_tokens

from ..variants import apply_variant, VARIANTS
from .realistic_prompts import CORPUS, CodePrompt


# regex helpers (operate on raw text; intentionally simple) ------------------
_FENCE_RE = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
_INLINE_RE = re.compile(r"`([^`\n]+)`")
_SIGNPOSTS = (
    "step by step", "Please note", "Please refer", "Please see",
    "do not modify", "do not deviate", "preserve the original indentation",
    "tool calls must be valid JSON", "must respond with",
)
_POLITE_PATTERNS = (
    "you are a helpful assistant", "you are a helpful ai assistant",
    "thank you", "i hope", "please be careful", "please be concise",
    "please respond carefully", "thank you for using",
)


def _fences(text: str) -> list[tuple[str, str]]:
    """Return list of (lang, body) for every fenced code block."""
    return [(m.group(1) or "", m.group(2)) for m in _FENCE_RE.finditer(text)]


def _inlines(text: str) -> set[str]:
    return {m.group(1) for m in _INLINE_RE.finditer(text)}


def _ast_dump_or_none(src: str) -> str | None:
    try:
        return ast.dump(ast.parse(src))
    except (SyntaxError, ValueError):
        return None


@dataclass
class CellMetrics:
    prompt_id: str
    variant: str

    chars_before: int
    chars_after: int
    tokens_before: int
    tokens_after: int
    char_savings_pct: float
    token_savings_pct: float

    fences_in: int
    fences_preserved: int
    inlines_in: int
    inlines_preserved: int
    signposts_in: int
    signposts_preserved: int
    polite_in: int
    polite_remaining: int

    py_blocks_in: int
    py_blocks_ast_stable: int
    py_blocks_parse_failed_after: int

    idempotent: bool
    invariants_pass: bool       # all hard invariants hold
    invariant_breakages: list   # which ones broke


def analyze_one(prompt: CodePrompt, variant: str) -> CellMetrics:
    before = prompt.text
    # variants apply only to system prompt; user is passed through
    after, _ = apply_variant(variant, before, "")

    # idempotency check
    after2, _ = apply_variant(variant, after, "")
    idem = (after2 == after)

    # tokens / chars
    cb, ca = len(before), len(after)
    tb, ta = estimate_tokens(before), estimate_tokens(after)
    cs = 100.0 * (cb - ca) / cb if cb else 0.0
    ts = 100.0 * (tb - ta) / tb if tb else 0.0

    # fences preserved (byte-exact body)
    f_in = _fences(before)
    after_bodies = {body for _, body in _fences(after)}
    f_preserved = sum(1 for _, body in f_in if body in after_bodies)

    # inline identifiers
    i_in = _inlines(before)
    i_preserved = sum(1 for s in i_in if f"`{s}`" in after)

    # signposts (case-sensitive lookups; corpus uses canonical casing)
    s_in = sum(1 for s in _SIGNPOSTS if s in before)
    s_preserved = sum(1 for s in _SIGNPOSTS if s in before and s in after)

    # politeness presence (case-insensitive — kpx removes case-folded matches)
    bl = before.lower()
    al = after.lower()
    p_in = sum(1 for p in _POLITE_PATTERNS if p in bl)
    p_remaining = sum(1 for p in _POLITE_PATTERNS if p in bl and p in al)

    # python AST stability for code blocks tagged python
    py_in = 0; py_stable = 0; py_failed = 0
    for lang, body in f_in:
        if lang.lower() not in ("py", "python", ""):
            continue
        ast_before = _ast_dump_or_none(body)
        if ast_before is None:
            continue
        py_in += 1
        # find a corresponding fence in after with same body
        if body in after_bodies:
            py_stable += 1
        else:
            # try parsing whatever block has the same lang tag
            after_same = [b for la, b in _fences(after) if la == lang]
            ok = False
            for cand in after_same:
                a = _ast_dump_or_none(cand)
                if a == ast_before:
                    py_stable += 1
                    ok = True
                    break
            if not ok:
                py_failed += 1

    # invariants
    breakages = []
    if f_in and f_preserved < len(f_in):
        breakages.append(f"fences {f_preserved}/{len(f_in)}")
    if i_in and i_preserved < len(i_in):
        breakages.append(f"inlines {i_preserved}/{len(i_in)}")
    if py_in and py_stable < py_in:
        breakages.append(f"py_ast {py_stable}/{py_in}")
    if not idem:
        breakages.append("non-idempotent")
    invariants_pass = not breakages

    return CellMetrics(
        prompt_id=prompt.id, variant=variant,
        chars_before=cb, chars_after=ca,
        tokens_before=tb, tokens_after=ta,
        char_savings_pct=cs, token_savings_pct=ts,
        fences_in=len(f_in), fences_preserved=f_preserved,
        inlines_in=len(i_in), inlines_preserved=i_preserved,
        signposts_in=s_in, signposts_preserved=s_preserved,
        polite_in=p_in, polite_remaining=p_remaining,
        py_blocks_in=py_in, py_blocks_ast_stable=py_stable,
        py_blocks_parse_failed_after=py_failed,
        idempotent=idem,
        invariants_pass=invariants_pass,
        invariant_breakages=breakages,
    )


def analyze_corpus(corpus: Iterable[CodePrompt] = CORPUS,
                   variants: Iterable[str] = VARIANTS) -> dict:
    cells = [analyze_one(p, v) for p in corpus for v in variants]

    # aggregates
    by_v: dict[str, list[CellMetrics]] = {}
    for c in cells:
        by_v.setdefault(c.variant, []).append(c)

    summary = {}
    for v, cs in by_v.items():
        n = len(cs)
        summary[v] = {
            "n": n,
            "tokens_before_mean": sum(c.tokens_before for c in cs) / n,
            "tokens_after_mean":  sum(c.tokens_after  for c in cs) / n,
            "token_savings_mean": sum(c.token_savings_pct for c in cs) / n,
            "char_savings_mean":  sum(c.char_savings_pct  for c in cs) / n,
            "fences_in_total":         sum(c.fences_in for c in cs),
            "fences_preserved_total":  sum(c.fences_preserved for c in cs),
            "inlines_in_total":        sum(c.inlines_in for c in cs),
            "inlines_preserved_total": sum(c.inlines_preserved for c in cs),
            "signposts_in_total":      sum(c.signposts_in for c in cs),
            "signposts_preserved_total": sum(c.signposts_preserved for c in cs),
            "polite_in_total":         sum(c.polite_in for c in cs),
            "polite_remaining_total":  sum(c.polite_remaining for c in cs),
            "py_blocks_in":            sum(c.py_blocks_in for c in cs),
            "py_blocks_ast_stable":    sum(c.py_blocks_ast_stable for c in cs),
            "idempotent_count":        sum(1 for c in cs if c.idempotent),
            "invariants_pass_count":   sum(1 for c in cs if c.invariants_pass),
            "breakages": sorted({b for c in cs for b in c.invariant_breakages}),
        }

    # by language slice
    by_lang: dict[str, list[CellMetrics]] = {}
    p_lookup = {p.id: p for p in corpus}
    for c in cells:
        lang = p_lookup[c.prompt_id].lang
        by_lang.setdefault((lang, c.variant), []).append(c)
    by_lang_summary = {}
    for (lang, v), cs in by_lang.items():
        by_lang_summary.setdefault(lang, {})[v] = {
            "n": len(cs),
            "token_savings_mean": sum(c.token_savings_pct for c in cs) / len(cs),
        }

    return {
        "cells": [asdict(c) for c in cells],
        "summary_by_variant": summary,
        "summary_by_lang_variant": by_lang_summary,
    }
