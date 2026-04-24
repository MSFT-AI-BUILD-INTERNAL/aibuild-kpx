"""Static audit of a prompt against the 30 Karpathy-aligned methods."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List

from kpx.tokens import estimate_tokens
from kpx.methods import (
    KNOWN_FACT_PATTERNS, _is_redundant_line, _ROLE_TAG_PATTERNS,
    _POLITE_PATTERNS, NO_FILLER_INSTRUCTION,
)


@dataclass
class Finding:
    method: str
    severity: str  # "info" | "warn" | "high"
    message: str
    estimated_savings_chars: int = 0


@dataclass
class AuditReport:
    tokens: int
    findings: List[Finding] = field(default_factory=list)

    @property
    def score(self) -> int:
        """0–100. 100 = no findings. Each finding deducts by severity weight."""
        weight = {"info": 1, "warn": 4, "high": 8}
        deduction = sum(weight[f.severity] for f in self.findings)
        return max(0, 100 - deduction)

    @property
    def recommendations(self) -> list[str]:
        return [f"[{f.method}/{f.severity}] {f.message}" for f in self.findings]


def audit(text: str) -> AuditReport:
    rep = AuditReport(tokens=estimate_tokens(text))

    # M03 — known facts
    hits = _count_pattern_hits(text, KNOWN_FACT_PATTERNS)
    if hits:
        rep.findings.append(Finding(
            "M03", "warn",
            f"{hits}건의 사전학습 일반 사실 문장 발견 — kpx compress -m M03 으로 제거.",
            estimated_savings_chars=hits * 80,
        ))

    # M04 — redundant system lines
    redundant = sum(1 for line in text.splitlines() if _is_redundant_line(line))
    if redundant:
        rep.findings.append(Finding(
            "M04", "warn",
            f"{redundant}개의 의례적 system 지시 — kpx compress -m M04.",
            estimated_savings_chars=redundant * 50,
        ))

    # M09 — filler instruction missing
    if NO_FILLER_INSTRUCTION not in text and ("system" in text.lower() or len(text) > 200):
        rep.findings.append(Finding(
            "M09", "info",
            "출력 filler 금지 지침 미포함 — kpx.methods.inject_no_filler() 권고.",
        ))

    # M24 — polite fillers
    polite_hits = _count_pattern_hits(text, _POLITE_PATTERNS)
    if polite_hits:
        rep.findings.append(Finding(
            "M24", "info",
            f"{polite_hits}건의 polite filler — kpx compress -m M24.",
            estimated_savings_chars=polite_hits * 12,
        ))

    # M25 — role tags
    tag_hits = _count_pattern_hits(text, _ROLE_TAG_PATTERNS)
    if tag_hits:
        rep.findings.append(Finding(
            "M25", "warn",
            f"{tag_hits}건의 채팅 템플릿 role 태그 중복 — kpx compress -m M25.",
            estimated_savings_chars=tag_hits * 15,
        ))

    # M01 — budget awareness (large file)
    if rep.tokens > 8000:
        rep.findings.append(Finding(
            "M01", "high",
            f"프롬프트 {rep.tokens} 토큰 — 8K 초과. 컨텍스트 윈도우 50% 룰 점검 필요.",
        ))

    # M19 — large doc → consider summary
    if rep.tokens > 4000:
        rep.findings.append(Finding(
            "M19", "info",
            "4K 토큰 초과 — kpx compress -m M19 (lossy summary) 또는 RAG 분할 검토.",
        ))

    # Recommendation-only methods (cannot statically apply but worth surfacing)
    _recommend_external_methods(text, rep)
    return rep


def _recommend_external_methods(text: str, rep: AuditReport) -> None:
    lower = text.lower()
    if "example:" in lower or "few-shot" in lower or text.count("\n```") >= 6:
        rep.findings.append(Finding(
            "M08", "info",
            "다수 few-shot 예시 감지 — ablation으로 최소 예시 수 N* 결정 권고.",
        ))
    if any(kw in lower for kw in ("cot", "chain-of-thought", "let's think")):
        rep.findings.append(Finding(
            "M10", "info",
            "CoT 문구 감지 — reasoning 모델로 위임 시 출력 토큰 절감 가능.",
        ))
    if rep.tokens > 1500 and ("system" in lower[:200]):
        rep.findings.append(Finding(
            "M11", "info",
            "장문 system prompt — Anthropic/OpenAI prompt caching 적용 권고 (정적 prefix).",
        ))


def _count_pattern_hits(text: str, patterns: list[str]) -> int:
    n = 0
    for pat in patterns:
        n += len(re.findall(pat, text))
    return n
