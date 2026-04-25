"""P4 — Calibration. kpx vs API-reported token counts (in-tokens only)."""
from __future__ import annotations
from pathlib import Path
from statistics import mean

from ._common import load_jsonl


def render(results_path: Path, out_dir: Path) -> Path:
    rows = load_jsonl(results_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "p4_calibration.md"

    pairs = [(r["tokens_in_kpx"], r["tokens_in_api"])
             for r in rows
             if r.get("tokens_in_kpx") and r.get("tokens_in_api")]
    if not pairs:
        out.write_text("# P4 Calibration\n\nNo paired token counts available "
                       "(adapter returned no usage).\n", encoding="utf-8")
        return out

    abs_err = [abs(k - a) for k, a in pairs]
    rel_err = [100.0 * (k - a) / a for k, a in pairs if a]
    over_predict = sum(1 for k, a in pairs if k > a) / len(pairs) * 100
    p50 = sorted(abs_err)[len(abs_err) // 2]
    p95 = sorted(abs_err)[max(0, int(len(abs_err) * 0.95) - 1)]

    lines = [
        "# kpx bench-real — P4 Calibration",
        "",
        f"- pairs: {len(pairs)}",
        f"- mean abs error: {mean(abs_err):.2f} tokens",
        f"- p50 abs error:  {p50}",
        f"- p95 abs error:  {p95}",
        f"- mean rel error: {mean(rel_err):+.2f}% (positive = kpx over-predicts)",
        f"- over-predict rate: {over_predict:.1f}%",
        "",
        "## Per-variant",
        "",
        "| Variant | n | mean kpx | mean api | mean rel err |",
        "|---|---:|---:|---:|---:|",
    ]
    by_v: dict[str, list[tuple[int, int]]] = {}
    for r in rows:
        if r.get("tokens_in_kpx") and r.get("tokens_in_api"):
            by_v.setdefault(r["variant"], []).append(
                (r["tokens_in_kpx"], r["tokens_in_api"]))
    for v in sorted(by_v):
        ps = by_v[v]
        ks = [k for k, _ in ps]
        as_ = [a for _, a in ps]
        rs = [100.0 * (k - a) / a for k, a in ps if a]
        lines.append(f"| {v} | {len(ps)} | {mean(ks):.1f} | {mean(as_):.1f} | "
                     f"{mean(rs):+.2f}% |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
