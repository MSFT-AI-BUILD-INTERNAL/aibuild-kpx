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
        "| Variant | n | tokens_in (mean) | Δtoken | quality_mean ±95%CI | Δquality | cost/quality point |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    rec = None
    for v in variants:
        rs = by_v[v]
        q = agg_quality(rs); tk = agg_tokens(rs)
        dt = reduction_pct(base_t, tk['mean'])
        dq = (q['mean'] or 0) - base_q
        total_cost = sum(float(r.get("cost_usd", 0.0) or 0.0) for r in rs)
        qsum = sum(float(r.get("quality_score", 0.0) or 0.0) for r in rs)
        cost_per_q = (total_cost / qsum) if qsum > 0 else 0.0
        ci = q.get("ci95") or 0.0
        lines.append(f"| {v} | {len(rs)} | {tk['mean']:.1f} | {-dt:+.2f}% | "
                     f"{q['mean']:.1f} ± {ci:.2f} | {dq:+.1f} | ${cost_per_q:.6f} |")
        # recommend the highest-saving variant with Δq >= -2
        if v != "V0" and dq >= -2.0:
            if rec is None or dt > rec[1]:
                rec = (v, dt, dq)

    lines += ["", "## Recommendation", ""]
    if rec:
        lines.append(f"**{rec[0]}** — {rec[1]:.2f}% token saving, Δquality {rec[2]:+.1f}")
    else:
        lines.append("No variant met the Δquality ≥ −2 threshold. Stay on V0.")

    lines += ["", "## Task-level risk view", "",
              "| Variant | Worst task | Mean quality | vs task V0 |",
              "|---|---|---:|---:|"]
    base_task_means = {}
    for task, rs in group_by(by_v.get("V0", []), "task").items():
        q = agg_quality(rs)
        base_task_means[task] = q.get("mean") or 0.0
    for v in variants:
        tmap = group_by(by_v[v], "task")
        worst_task = "-"
        worst_mean = None
        worst_delta = 0.0
        for task, rs in tmap.items():
            qmean = agg_quality(rs).get("mean")
            if qmean is None:
                continue
            base_task = base_task_means.get(task, 0.0)
            delta = qmean - base_task
            if worst_mean is None or qmean < worst_mean:
                worst_task = task
                worst_mean = qmean
                worst_delta = delta
        if worst_mean is None:
            lines.append(f"| {v} | - | - | - |")
        else:
            lines.append(f"| {v} | {worst_task} | {worst_mean:.1f} | {worst_delta:+.1f} |")

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
