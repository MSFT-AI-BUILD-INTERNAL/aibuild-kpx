"""Unit tests for bench_real.render_results_panel (F17)."""
from __future__ import annotations
import json
import pytest
from pathlib import Path

from bench_real.render_results_panel import (
    _markers, _list_panels, _patch_doc, _load_per_variant,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def test_markers_format():
    s, e = _markers("07b")
    assert s == "<!-- panel:07b:start"
    assert e == "<!-- panel:07b:end -->"
    s2, _ = _markers("ab-12_X")
    assert s2 == "<!-- panel:ab-12_X:start"


def test_list_panels_order_and_dedup(tmp_path: Path):
    doc = tmp_path / "d.html"
    doc.write_text(
        "x <!-- panel:alpha:start --> a <!-- panel:alpha:end -->\n"
        "y <!-- panel:beta:start --> b <!-- panel:beta:end -->\n"
        "z <!-- panel:alpha:start --> a2 <!-- panel:alpha:end -->\n",
        encoding="utf-8",
    )
    assert _list_panels(doc) == ["alpha", "beta"]


def test_list_panels_empty(tmp_path: Path):
    doc = tmp_path / "d.html"
    doc.write_text("<html>nothing here</html>", encoding="utf-8")
    assert _list_panels(doc) == []


def _make_doc(tmp_path: Path) -> Path:
    doc = tmp_path / "d.html"
    doc.write_text(
        "HEAD\n<!-- panel:zzz:start -->\nOLD\n<!-- panel:zzz:end -->\nTAIL\n",
        encoding="utf-8",
    )
    return doc


# Fragments mirror real _render output: they contain both markers.
FRAG_OLD = ("<!-- panel:zzz:start -->\nOLD\n"
            "<!-- panel:zzz:end -->\n")
FRAG_NEW = ("<!-- panel:zzz:start -->\nNEW\n"
            "<!-- panel:zzz:end -->\n")


def test_patch_doc_replaces_region(tmp_path: Path):
    doc = _make_doc(tmp_path)
    _patch_doc(doc, FRAG_NEW, panel="zzz")
    text = doc.read_text()
    assert "OLD" not in text
    assert "NEW" in text
    assert text.startswith("HEAD\n")
    assert text.endswith("TAIL\n")


def test_patch_doc_idempotent(tmp_path: Path):
    doc = _make_doc(tmp_path)
    _patch_doc(doc, FRAG_NEW, panel="zzz")
    first = doc.read_text()
    _patch_doc(doc, FRAG_NEW, panel="zzz")
    assert doc.read_text() == first


def test_patch_doc_backup(tmp_path: Path):
    doc = _make_doc(tmp_path)
    original = doc.read_text()
    _patch_doc(doc, FRAG_NEW, panel="zzz", backup=True)
    bak = doc.with_suffix(doc.suffix + ".bak")
    assert bak.exists()
    assert bak.read_text() == original


def test_patch_doc_dry_run_does_not_write(tmp_path: Path, capsys):
    doc = _make_doc(tmp_path)
    original = doc.read_text()
    _patch_doc(doc, FRAG_NEW, panel="zzz", dry_run=True)
    assert doc.read_text() == original
    out = capsys.readouterr().out
    assert "OLD" in out and "NEW" in out
    assert out.startswith("--- ")


def test_patch_doc_dry_run_no_change(tmp_path: Path, capsys):
    doc = _make_doc(tmp_path)
    _patch_doc(doc, FRAG_OLD, panel="zzz", dry_run=True)
    out = capsys.readouterr().out
    assert "no change" in out


def test_patch_doc_wrong_panel_exits(tmp_path: Path):
    doc = _make_doc(tmp_path)
    original = doc.read_text()
    with pytest.raises(SystemExit):
        _patch_doc(doc, FRAG_NEW, panel="missing")
    assert doc.read_text() == original  # untouched


def test_patch_doc_diff_out(tmp_path: Path):
    doc = _make_doc(tmp_path)
    diff_path = tmp_path / "patch.diff"
    _patch_doc(doc, FRAG_NEW, panel="zzz", dry_run=True, diff_out=diff_path)
    assert diff_path.exists()
    diff = diff_path.read_text()
    assert "OLD" in diff and "NEW" in diff
    assert diff.startswith("--- ")


def test_load_per_variant_aggregates(tmp_path: Path):
    runs = tmp_path / "runs"
    runs.mkdir()
    _write_jsonl(runs / "m1.jsonl", [
        {"model": "vendor/m1", "variant": "V0", "quality_score": 80.0,
         "tokens_in_api": 100},
        {"model": "vendor/m1", "variant": "V0", "quality_score": 60.0,
         "tokens_in_api": 200},
        {"model": "vendor/m1", "variant": "V4", "quality_score": 90.0,
         "tokens_in_api": 50},
        {"model": "vendor/m1", "variant": "V4", "quality_score": 90.0,
         "tokens_in_api": 50,
         "judge_axes": {"fallback": "rule_based", "rule_based_score": 90}},
    ])
    out = _load_per_variant(runs)
    assert "vendor/m1" in out
    v0 = out["vendor/m1"]["V0"]
    assert v0["q"] == 70.0
    assert v0["tok_in"] == 150.0
    assert v0["n"] == 2
    assert v0["fb"] == 0
    v4 = out["vendor/m1"]["V4"]
    assert v4["fb"] == 1  # F9 fallback counted


def test_load_per_variant_skips_errors(tmp_path: Path):
    runs = tmp_path / "runs"
    runs.mkdir()
    _write_jsonl(runs / "m1.jsonl", [
        {"model": "m", "variant": "V0", "quality_score": 80.0,
         "tokens_in_api": 100},
        {"model": "m", "variant": "V0", "error": "boom"},
    ])
    out = _load_per_variant(runs)
    assert out["m"]["V0"]["n"] == 1
