"""P2 — Executive summary. 1-page Markdown."""
from __future__ import annotations
from pathlib import Path

from ._common import load_jsonl, group_by, agg_quality, agg_tokens, reduction_pct
from ..cost_cap import PRICES


def render(results_path: Path, out_dir: Path) -> Path:
    rows = load_jsonl(results_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "p2_exec_summary.md"

    by_v = group_by(rows, "variant")
    variants = sorted(by_v.keys())
    if not rows:
        out.write_text("# kpx bench-real — Exec Summary\n\nNo results.\n")
        return out

    base_q = agg_quality(by_v["V0"]).get("mean") or 0.0
    base_t = agg_tokens(by_v["V0"]).get("mean") or 0.0
    model = rows[0].get("model", "?")

    lines = [
        "# kpx bench-real — Executive Summary",
        f"_n={len(rows)} cells · model={model}_",
        "",
        "## Token reduction × Quality (vs V0)",
        "",
        "| Variant | n | tokens_in (mean) | Δtoken | quality_mean | Δquality |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    rec = None
    for v in variants:
        rs = by_v[v]
        q = agg_quality(rs); tk = agg_tokens(rs)
        dt = reduction_pct(base_t, tk['mean'])
        dq = (q['mean'] or 0) - base_q
        lines.append(f"| {v} | {len(rs)} | {tk['mean']:.1f} | {-dt:+.2f}% | "
                     f"{q['mean']:.1f} | {dq:+.1f} |")
        # recommend the highest-saving variant with Δq >= -2
        if v != "V0" and dq >= -2.0:
            if rec is None or dt > rec[1]:
                rec = (v, dt, dq)

    lines += ["", "## Recommendation", ""]
    if rec:
        lines.append(f"**{rec[0]}** — {rec[1]:.2f}% token saving, Δquality {rec[2]:+.1f}")
    else:
        lines.append("No variant met the Δquality ≥ −2 threshold. Stay on V0.")

    # Monthly $ scenarios (input-only, since kpx affects input only)
    pin, _pout = PRICES.get(model, (1.0, 3.0))
    lines += ["", "## Cost scenarios (input tokens only)", ""]
    lines.append("| QPS | tokens/req | Monthly input tokens | V0 cost | "
                 + " | ".join(f"{v} cost" for v in variants if v != "V0") + " |")
    lines.append("|---:|---:|---:|---:|" + "---:|" * (len(variants) - 1))
    qps_table = [(0.1, base_t), (1, base_t), (10, base_t)]
    for qps, tok in qps_table:
        monthly_tok = qps * 60 * 60 * 24 * 30 * tok
        v0c = monthly_tok / 1e6 * pin
        cells = [f"${v0c:,.2f}"]
        for v in variants:
            if v == "V0":
                continue
            tk = agg_tokens(by_v[v])['mean']
            c = (qps * 60 * 60 * 24 * 30 * tk) / 1e6 * pin
            cells.append(f"${c:,.2f}")
        lines.append(f"| {qps} | {tok:.0f} | {monthly_tok:,.0f} | " + " | ".join(cells) + " |")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
