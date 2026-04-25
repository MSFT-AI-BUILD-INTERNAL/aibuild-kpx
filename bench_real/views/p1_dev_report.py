"""P1 — Developer report. Filterable HTML with per-task × variant heatmap."""
from __future__ import annotations
from pathlib import Path

from ._common import load_jsonl, group_by, agg_quality, agg_tokens, reduction_pct


def render(results_path: Path, out_dir: Path) -> Path:
    rows = load_jsonl(results_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "p1_dev_report.html"

    tasks = sorted({r["task"] for r in rows})
    variants = sorted({r["variant"] for r in rows})
    by_tv = group_by(rows, "task", "variant")
    by_v = group_by(rows, "variant")

    # baseline V0 per task
    base_q = {t: agg_quality(by_tv.get((t, "V0"), [])).get("mean") for t in tasks}
    base_tok = {t: agg_tokens(by_tv.get((t, "V0"), [])).get("mean") for t in tasks}

    def cell(task, v):
        rs = by_tv.get((task, v), [])
        if not rs:
            return "<td class='na'>—</td>"
        q = agg_quality(rs); tk = agg_tokens(rs)
        dq = (q["mean"] - (base_q[task] or 0)) if (base_q[task] is not None and q["mean"] is not None) else 0.0
        dt = reduction_pct(base_tok[task] or 0, tk["mean"])
        cls = "good" if (dt > 5 and dq >= -2) else ("warn" if dq < -5 else "")
        qm = f"{q['mean']:.1f}" if q['mean'] is not None else "—"
        return (f"<td class='{cls}'>"
                f"<div class='q'>{qm}</div>"
                f"<div class='t'>tok {tk['mean']:.0f} ({-dt:+.1f}%)</div>"
                f"<div class='d'>Δq {dq:+.1f}</div>"
                f"</td>")

    rows_html = []
    for t in tasks:
        rows_html.append(f"<tr><th>{t}</th>" + "".join(cell(t, v) for v in variants) + "</tr>")

    # overall row
    overall_q_v0 = agg_quality(by_v.get("V0", [])).get("mean")
    overall_t_v0 = agg_tokens(by_v.get("V0", [])).get("mean")
    over = ["<tr class='overall'><th>ALL</th>"]
    for v in variants:
        rs = by_v.get(v, [])
        q = agg_quality(rs); tk = agg_tokens(rs)
        dq = (q['mean'] - (overall_q_v0 or 0)) if q['mean'] is not None else 0.0
        dt = reduction_pct(overall_t_v0 or 0, tk['mean'])
        qm = f"{q['mean']:.1f}" if q['mean'] is not None else "—"
        over.append(f"<td><div class='q'>{qm}</div>"
                    f"<div class='t'>tok {tk['mean']:.0f} ({-dt:+.1f}%)</div>"
                    f"<div class='d'>Δq {dq:+.1f}</div></td>")
    over.append("</tr>")

    html = f"""<!doctype html><html lang=en><meta charset=utf-8>
<title>kpx bench-real · P1 dev report</title>
<style>
body{{background:#0b0d10;color:#e8e8e8;font:14px/1.5 system-ui,-apple-system,sans-serif;padding:24px}}
h1{{margin:0 0 4px}}.sub{{color:#888;margin-bottom:24px}}
table{{border-collapse:collapse;width:100%;margin-top:16px}}
th,td{{border:1px solid #222;padding:8px;text-align:center;vertical-align:top;min-width:120px}}
th{{background:#15181c;color:#bbb;font-weight:600}}
td .q{{font-size:18px;font-weight:600}}
td .t{{color:#888;font-size:11px;margin-top:2px}}
td .d{{color:#666;font-size:10px}}
td.good{{background:#0d2417}} td.warn{{background:#2a1010}} td.na{{color:#444}}
tr.overall th,tr.overall td{{background:#15181c;font-weight:700}}
.legend{{margin-top:16px;color:#888;font-size:12px}}
.legend code{{background:#15181c;padding:2px 6px;border-radius:3px;color:#ddd}}
</style>
<body>
<h1>kpx bench-real — P1 Developer Report</h1>
<div class=sub>n={len(rows)} cells · tasks={len(tasks)} · variants={','.join(variants)}</div>
<table>
<thead><tr><th>Task</th>{''.join(f'<th>{v}</th>' for v in variants)}</tr></thead>
<tbody>
{''.join(rows_html)}
{''.join(over)}
</tbody>
</table>
<div class=legend>
Each cell shows <code>quality_mean</code> (top), token-in <code>kpx_count (Δ vs V0)</code>, and <code>Δquality vs V0</code>.
Green = ≥5% token saving with ≤2pt quality drop. Red = &gt;5pt quality drop.
</div>
</body></html>
"""
    out.write_text(html, encoding="utf-8")
    return out
