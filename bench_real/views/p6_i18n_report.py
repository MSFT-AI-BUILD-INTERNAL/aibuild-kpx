"""P6 — i18n report. Per-language token reduction and quality delta."""
from __future__ import annotations
from pathlib import Path

from ._common import load_jsonl, group_by, agg_quality, agg_tokens, reduction_pct


def render(results_path: Path, out_dir: Path) -> Path:
    rows = load_jsonl(results_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "p6_i18n_report.md"

    if not rows:
        out.write_text("# P6 i18n\n\nNo results.\n", encoding="utf-8")
        return out

    by_lv = group_by(rows, "lang", "variant")
    langs = sorted({r.get("lang", "?") for r in rows})
    variants = sorted({r["variant"] for r in rows})

    lines = [
        "# kpx bench-real — P6 i18n Report",
        "",
        "Token reduction (vs V0) and Δquality per language.",
        "",
        "| Lang | Variant | n | tok_in_kpx | Δtoken% | quality | Δquality |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for lang in langs:
        v0 = by_lv.get((lang, "V0"), [])
        base_t = agg_tokens(v0)["mean"] if v0 else 0
        base_q = agg_quality(v0)["mean"] if v0 else 0
        for v in variants:
            rs = by_lv.get((lang, v), [])
            if not rs:
                continue
            q = agg_quality(rs); tk = agg_tokens(rs)
            dt = reduction_pct(base_t, tk["mean"]) if base_t else 0.0
            dq = ((q["mean"] or 0) - (base_q or 0))
            lines.append(f"| {lang} | {v} | {len(rs)} | {tk['mean']:.1f} | "
                         f"{-dt:+.2f}% | {q['mean']:.1f} | {dq:+.1f} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
