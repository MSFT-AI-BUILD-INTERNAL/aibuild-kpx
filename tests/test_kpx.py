"""kpx test suite."""
from kpx import audit, compress, estimate_tokens
from kpx.methods import (
    strip_known_facts, strip_polite, strip_role_tags,
    minimize_system_prompt, lossy_summary, format_compare,
    inject_no_filler, NO_FILLER_INSTRUCTION,
)
from kpx.tokens import fits_window


def test_estimate_tokens_basic():
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello world") > 0
    assert estimate_tokens("한글 테스트") > 0


def test_strip_known_facts():
    text = "Python is a high-level interpreted language. Now do X."
    out = strip_known_facts(text)
    assert "Python is a" not in out
    assert "Now do X" in out


def test_strip_polite():
    text = "Please write the code. Thank you so much. Now do X."
    out = strip_polite(text)
    assert "Please" not in out
    assert "Thank you so much" not in out
    assert "Now do X" in out


def test_strip_role_tags():
    text = "<|system|>You are nice<|im_end|>\n[INST] hi [/INST]\n### Instruction: do X"
    out = strip_role_tags(text)
    assert "<|" not in out
    assert "[INST]" not in out
    assert "### Instruction" not in out
    assert "do X" in out


def test_minimize_system_prompt():
    text = "You are a helpful assistant.\nDo task X.\nPlease respond carefully."
    cleaned, removed = minimize_system_prompt(text)
    assert "Do task X" in cleaned
    assert any("helpful assistant" in r for r in removed)


def test_lossy_summary_passthrough_short():
    text = "short text"
    assert lossy_summary(text, max_chars=100) == text


def test_lossy_summary_long():
    text = "# Title\n\n" + ("This is sentence one. This is sentence two. " * 200)
    out = lossy_summary(text, max_chars=200)
    assert len(out) <= 250
    assert "# Title" in out


def test_format_compare_list_of_dicts():
    data = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    rows = format_compare(data)
    formats = [r.format for r in rows]
    assert "json-min" in formats
    assert "markdown-table" in formats
    assert rows == sorted(rows, key=lambda r: r.chars)


def test_inject_no_filler_idempotent():
    base = "system: do X"
    once = inject_no_filler(base)
    twice = inject_no_filler(once)
    assert NO_FILLER_INSTRUCTION in once
    assert once == twice


def test_compress_chain():
    text = (
        "<|system|>You are a helpful assistant.\n"
        "Please write a function. Thank you. "
        "Python is a high-level interpreted language. "
        "Now do X."
    )
    out = compress(text)
    assert "<|" not in out
    assert "Please" not in out
    assert "Python is a" not in out
    assert "Now do X" in out
    assert estimate_tokens(out) < estimate_tokens(text)


def test_audit_score_clean():
    text = "Do X."
    rep = audit(text)
    assert rep.score >= 90


def test_audit_finds_issues():
    text = (
        "<|system|>You are a helpful assistant. "
        "Please do X. Thank you. "
        "Python is a high-level interpreted language."
    )
    rep = audit(text)
    method_ids = {f.method for f in rep.findings}
    assert "M03" in method_ids
    assert "M24" in method_ids
    assert "M25" in method_ids
    assert rep.score < 100


def test_fits_window():
    assert fits_window("hi", 1000) is True
    big = "x" * 100_000
    assert fits_window(big, 200_000, ratio=0.05) is False


def test_compress_unknown_method():
    import pytest
    with pytest.raises(ValueError):
        compress("text", methods=["M99"])
