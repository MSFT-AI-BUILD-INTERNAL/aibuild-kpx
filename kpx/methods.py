"""Implementations of token-optimization methods (M01~M30).

Only methods that can be applied to a prompt string statically (without an
external LLM call) are implemented. Others are surfaced as recommendations
by kpx.audit.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterable


# ---------------------------------------------------------------------------
# M03 — strip facts the model already knows from pretraining
# ---------------------------------------------------------------------------
# Heuristic: remove sentences that match well-known textbook patterns.
KNOWN_FACT_PATTERNS = [
    r"(?i)\bpython\s+is\s+(?:a|an)\s+(?:high-?level|interpreted|dynamic)[^.\n]*\.",
    r"(?i)\b(?:javascript|js)\s+is\s+(?:a|an)\s+[^.\n]*\.",
    r"(?i)\bhttp\s+stands\s+for[^.\n]*\.",
    r"(?i)\bjson\s+stands\s+for[^.\n]*\.",
    r"(?i)\bsql\s+stands\s+for[^.\n]*\.",
    r"(?i)\bgit\s+is\s+(?:a|an)\s+(?:distributed\s+)?version\s+control[^.\n]*\.",
    r"(?i)\bdocker\s+is\s+(?:a|an)?\s*(?:containerization|container\s+platform)[^.\n]*\.",
    r"(?i)\bas\s+you\s+(?:probably\s+)?know[^,.\n]*[,.]",
    r"(?i)\bit\s+is\s+well[- ]known\s+that[^,.\n]*[,.]",
]


def strip_known_facts(text: str) -> str:
    out = text
    for pat in KNOWN_FACT_PATTERNS:
        out = re.sub(pat, "", out)
    return _collapse_blank_lines(out)


# ---------------------------------------------------------------------------
# M04 — system prompt minimizer (lint)
# ---------------------------------------------------------------------------
def minimize_system_prompt(text: str) -> tuple[str, list[str]]:
    """Apply low-risk system-prompt cleanups; return (cleaned, removed_lines)."""
    removed: list[str] = []
    out_lines: list[str] = []
    for line in text.splitlines():
        if _is_redundant_line(line):
            removed.append(line.strip())
            continue
        out_lines.append(line)
    cleaned = "\n".join(out_lines)
    return _collapse_blank_lines(cleaned), removed


_REDUNDANT_PHRASES = (
    "you are a helpful assistant",
    "you are an ai",
    "do your best",
    "think step by step",  # only useful if not already in system; conservative removal
    "let's think step by step",
    "please respond",
    "please provide",
)


def _is_redundant_line(line: str) -> bool:
    s = line.strip().lower()
    if not s:
        return False
    if len(s) < 5:
        return False
    return any(p in s for p in _REDUNDANT_PHRASES)


# ---------------------------------------------------------------------------
# M09 — output filler instruction injector
# ---------------------------------------------------------------------------
NO_FILLER_INSTRUCTION = (
    "Output rules: no preamble, no postamble, no apologies, no restating the "
    "question. Direct answer only."
)


def inject_no_filler(system_prompt: str) -> str:
    if NO_FILLER_INSTRUCTION in system_prompt:
        return system_prompt
    sep = "\n\n" if system_prompt and not system_prompt.endswith("\n") else ""
    return f"{system_prompt}{sep}{NO_FILLER_INSTRUCTION}"


# ---------------------------------------------------------------------------
# M15 — serialization format comparison
# ---------------------------------------------------------------------------
@dataclass
class FormatBenchmark:
    format: str
    chars: int
    rendered: str


def format_compare(data: dict | list) -> list[FormatBenchmark]:
    """Return char counts of the same data in 4 formats. Lower = fewer tokens.

    Markdown table is computed only when data is a list[dict] with uniform keys.
    """
    import json
    out: list[FormatBenchmark] = []
    j = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out.append(FormatBenchmark("json-min", len(j), j))

    j2 = json.dumps(data, ensure_ascii=False, indent=2)
    out.append(FormatBenchmark("json-pretty", len(j2), j2))

    try:
        import yaml  # type: ignore
        y = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        out.append(FormatBenchmark("yaml", len(y), y))
    except ImportError:
        pass

    md = _to_markdown_table(data)
    if md is not None:
        out.append(FormatBenchmark("markdown-table", len(md), md))

    return sorted(out, key=lambda b: b.chars)


def _to_markdown_table(data) -> str | None:
    if not isinstance(data, list) or not data:
        return None
    if not all(isinstance(r, dict) for r in data):
        return None
    keys = list(data[0].keys())
    if not all(set(r.keys()) == set(keys) for r in data):
        return None
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    rows = ["| " + " | ".join(str(r[k]) for k in keys) + " |" for r in data]
    return "\n".join([header, sep, *rows])


# ---------------------------------------------------------------------------
# M19 — lossy summary (heuristic, no LLM)
# ---------------------------------------------------------------------------
def lossy_summary(text: str, max_chars: int = 2000) -> str:
    """Extractive: keep headings + first sentence of each paragraph + bullets."""
    if len(text) <= max_chars:
        return text
    lines = text.splitlines()
    keep: list[str] = []
    in_para = False
    for line in lines:
        s = line.strip()
        if not s:
            in_para = False
            keep.append("")
            continue
        if s.startswith("#") or s.startswith("- ") or s.startswith("* ") or s.startswith("|"):
            keep.append(line)
            in_para = False
            continue
        if not in_para:
            # first sentence of paragraph
            m = re.match(r"^(.*?[.!?。！？])(\s|$)", s)
            keep.append(line if not m else line[: len(m.group(1))])
            in_para = True
    out = _collapse_blank_lines("\n".join(keep))
    if len(out) > max_chars:
        out = out[:max_chars].rsplit("\n", 1)[0] + "\n…[truncated]"
    return out


# ---------------------------------------------------------------------------
# M24 — polite filler stripper
# ---------------------------------------------------------------------------
_POLITE_PATTERNS = [
    r"(?i)\b(?:please|kindly)\s+",
    r"(?i)\bthank\s+you[^.\n]*\.",
    r"(?i)\bthanks\s+(?:in\s+advance|so\s+much)[^.\n]*\.",
    r"(?i)\bI'd\s+(?:like|love)\s+(?:you\s+)?to\s+",
    r"(?i)\bif\s+you\s+(?:could|don't\s+mind)[^,.\n]*[,.]",
    r"(?i)\bwould\s+you\s+(?:please\s+)?",
]


def strip_polite(text: str) -> str:
    out = text
    for pat in _POLITE_PATTERNS:
        out = re.sub(pat, "", out)
    return out


# ---------------------------------------------------------------------------
# M25 — remove duplicated chat-template role tags
# ---------------------------------------------------------------------------
_ROLE_TAG_PATTERNS = [
    r"<\|?(?:system|user|assistant|im_start|im_end)\|?>",
    r"\[INST\]|\[/INST\]",
    r"###\s*(?:Instruction|Response|Input):\s*",
]


def strip_role_tags(text: str) -> str:
    out = text
    for pat in _ROLE_TAG_PATTERNS:
        out = re.sub(pat, "", out)
    return _collapse_blank_lines(out)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip() + ("\n" if text.endswith("\n") else "")


# Public registry used by audit/compress
SAFE_TRANSFORMS: dict[str, callable] = {
    "M03": strip_known_facts,
    "M04": lambda t: minimize_system_prompt(t)[0],
    "M19": lossy_summary,
    "M24": strip_polite,
    "M25": strip_role_tags,
}
