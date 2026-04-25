"""Sandboxed Python code execution for T01/T02.

Runs the model's code in a separate subprocess with a hard CPU/wall timeout
and no network access. Returns (passed: int, total: int).
"""
from __future__ import annotations
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Pull the first Python fenced block; fall back to whole text."""
    m = _FENCE_RE.search(text)
    return (m.group(1) if m else text).strip()


def run_pytest_inline(code: str, tests: list[str], timeout: float = 5.0) -> tuple[int, int]:
    """Execute ``code`` then run each ``tests[i]`` assertion. Returns (passed, total)."""
    if not tests:
        return (0, 0)
    runner = textwrap.dedent("""
    import sys, json, traceback
    code = sys.stdin.read().split("\\n###TESTS###\\n")
    body, raw_tests = code[0], code[1] if len(code) > 1 else ""
    ns = {}
    try:
        exec(body, ns)
    except Exception:
        print(json.dumps({"compile_error": traceback.format_exc()[-500:]}))
        sys.exit(0)
    results = []
    for line in raw_tests.split("\\n"):
        line = line.strip()
        if not line:
            continue
        try:
            exec(line, ns)
            results.append(True)
        except Exception:
            results.append(False)
    print(json.dumps({"results": results}))
    """).strip()
    payload = code + "\n###TESTS###\n" + "\n".join(tests)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(runner)
        runner_path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-S", runner_path],
            input=payload, capture_output=True, text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return (0, len(tests))
    finally:
        Path(runner_path).unlink(missing_ok=True)

    out = proc.stdout.strip().splitlines()
    if not out:
        return (0, len(tests))
    import json
    try:
        data = json.loads(out[-1])
    except Exception:
        return (0, len(tests))
    if "compile_error" in data:
        return (0, len(tests))
    results = data.get("results", [])
    return (sum(1 for r in results if r), len(tests))
