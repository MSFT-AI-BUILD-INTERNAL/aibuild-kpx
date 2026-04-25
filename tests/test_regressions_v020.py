"""Regression tests for v0.2.0 fixes (B1, B2, B3, B10, B11, idempotency, stdin)."""
import subprocess
import sys

import pytest

from kpx import compress
from kpx.methods import (
    minimize_system_prompt, strip_polite, strip_known_facts,
    strip_role_tags, lossy_summary, inject_no_filler,
)
from kpx.audit import audit


# ---- B1: CoT preserved (Karpathy advocates) ---------------------------------

def test_b1_cot_phrases_preserved():
    for cot in ("think step by step", "Let's think step by step", "chain-of-thought"):
        text = f"You are a tutor. {cot}. Solve x^2."
        out, removed = minimize_system_prompt(text)
        assert cot in out, f"{cot!r} should NOT be removed by minimize_system_prompt"
        assert not any(cot in r for r in removed)


# ---- B2: technical signposts preserved --------------------------------------

@pytest.mark.parametrize("phrase", [
    "Please note", "Please refer to", "Please see", "Please check",
    "Please find", "Please consult", "Please observe", "Please notice",
])
def test_b2_signposts_preserved(phrase):
    text = f"{phrase} the appendix for details."
    assert phrase in strip_polite(text)


def test_b2_polite_filler_still_stripped():
    text = "Please write the function."
    out = strip_polite(text)
    assert "Please" not in out
    assert "write the function" in out


# ---- B3: multi-clause line not over-removed ---------------------------------

def test_b3_multi_clause_line_kept():
    # line contains "you are an AI" substring but most of the line is real content
    text = (
        "You are an AI helper that solves complex symbolic integration "
        "problems for graduate students. Now solve: integral of x^2 dx."
    )
    out, removed = minimize_system_prompt(text)
    assert "integration" in out
    assert "symbolic" in out


def test_b3_pure_redundant_line_still_removed():
    text = "You are a helpful assistant.\nDo task X."
    out, _ = minimize_system_prompt(text)
    assert "You are a helpful assistant" not in out
    assert "Do task X" in out


# ---- B10: code blocks protected ---------------------------------------------

def test_b10_strip_known_facts_skips_code_fence():
    text = (
        "Outside fact: Python is a high-level interpreted language.\n"
        "```\n# Inside: Python is a high-level interpreted language.\n```\n"
    )
    out = strip_known_facts(text)
    assert "Outside fact:" in out
    assert "Outside fact: Python is a high-level" not in out  # outside removed
    assert "Inside: Python is a high-level interpreted language" in out  # inside preserved


def test_b10_strip_polite_skips_inline_code():
    text = "Please write `please use foo` carefully."
    out = strip_polite(text)
    assert "`please use foo`" in out  # backticked content preserved


# ---- B11: whitespace cleanup after role tag stripping -----------------------

def test_b11_no_double_spaces_after_strip():
    text = "<|system|>  Hello  [INST] there [/INST]  world"
    out = strip_role_tags(text)
    assert "  " not in out
    assert "Hello" in out and "there" in out and "world" in out


# ---- M19 lossy_summary improvements -----------------------------------------

def test_m19_flat_text_keeps_substantial_content():
    text = ("This is sentence. " * 500)
    out = lossy_summary(text, max_chars=500)
    assert len(out) > 100, "should not collapse to near-empty"
    assert "This is sentence" in out


def test_m19_idempotent_on_already_truncated():
    text = ("para. " * 1000)
    once = lossy_summary(text, max_chars=300)
    twice = lossy_summary(once, max_chars=300)
    assert once == twice


# ---- compress idempotency property test -------------------------------------

@pytest.mark.parametrize("text", [
    "<|system|>You are a helpful assistant. Please do X. Thank you. Now do X.",
    "Refactor:\n```py\n# Python is a high-level lang\n```\nThank you.",
    "# Title\n\nPara one. Para two.\n\n## Sub\n\n- bullet",
    "한글 문서. " * 50 + "감사합니다.",
    "Please note: critical. Please write code. Thank you.",
])
def test_compress_idempotent(text):
    once = compress(text)
    twice = compress(once)
    assert once == twice, f"compress not idempotent on input {text!r}"


# ---- audit M09 trigger refined ----------------------------------------------

def test_audit_m09_not_triggered_on_plain_user_text():
    text = "x" * 500  # long but not system-prompt-shaped
    rep = audit(text)
    methods = {f.method for f in rep.findings}
    assert "M09" not in methods


def test_audit_m09_triggered_on_system_shaped_text():
    text = "You are a helpful assistant. Do X."
    rep = audit(text)
    methods = {f.method for f in rep.findings}
    assert "M09" in methods


# ---- CLI stdin support ------------------------------------------------------

def _run_cli(args, stdin_text):
    return subprocess.run(
        [sys.executable, "-m", "kpx.cli", *args],
        input=stdin_text, capture_output=True, text=True,
    )


def test_cli_audit_stdin():
    r = _run_cli(["audit", "-"], "You are a helper. Please do X. Thank you.")
    assert r.returncode == 0
    assert "score" in r.stdout
    assert "<stdin>" in r.stdout


def test_cli_compress_stdin():
    r = _run_cli(["compress", "-"], "Please write code. Thank you.")
    assert r.returncode == 0
    assert "Please" not in r.stdout


def test_cli_budget_stdin():
    r = _run_cli(["budget", "-", "--window", "1000"], "hello")
    assert r.returncode == 0
    assert "tokens:" in r.stdout
    assert "fits 50% rule" in r.stdout
