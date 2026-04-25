"""kpx CLI entrypoint."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from kpx import __version__
from kpx.audit import audit
from kpx.compress import compress
from kpx.tokens import estimate_tokens, fits_window
from kpx.methods import SAFE_TRANSFORMS, format_compare


METHODS_TABLE = [
    ("M01", "RAM 인지", "F1", "audit"),
    ("M02", "Just the right info", "F3", "manual"),
    ("M03", "사전학습 사실 제거", "F8", "compress"),
    ("M04", "System prompt 최소화", "F2", "compress"),
    ("M05", "Tool 스키마 압축", "F2+F3", "manual"),
    ("M06", "RAG next-step 한정", "F3", "manual"),
    ("M07", "슬라이딩 윈도우", "F1+F4", "external"),
    ("M08", "Few-shot 예산", "F5+F2", "audit"),
    ("M09", "Filler 금지 지침", "F2+F7", "inject"),
    ("M10", "Reasoning 위임", "F1+F5", "audit"),
    ("M11", "Prompt caching", "F1", "audit"),
    ("M12", "Speculative decoding", "F1", "external"),
    ("M13", "Tokenizer-aware", "F2", "manual"),
    ("M14", "코드 vs 자연어", "F2", "manual"),
    ("M15", "직렬화 포맷 비교", "F1+F2", "compare"),
    ("M16", "임베딩 사전필터", "F3", "external"),
    ("M17", "Tool 호출 ≫ dump", "F1+F3", "manual"),
    ("M18", "외부 메모리", "F4", "external"),
    ("M19", "Lossy 요약", "F8 메타", "compress"),
    ("M20", "Verifiability", "F5", "external"),
    ("M21", "Vibe coding", "F6", "manual"),
    ("M22", "멀티 에이전트", "F1+F3", "external"),
    ("M23", "페르소나 일관성", "F7", "manual"),
    ("M24", "Polite filler", "F2", "compress"),
    ("M25", "role 태그 중복 제거", "F2", "compress"),
    ("M26", "Early termination", "F5", "manual"),
    ("M27", "Constrained decoding", "F5+F2", "external"),
    ("M28", "양자화", "F1", "external"),
    ("M29", "Distillation", "F8", "external"),
    ("M30", "종합 적용 순서", "all", "guide"),
]


def _read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def cmd_audit(args) -> int:
    text = _read_input(args.file)
    rep = audit(text)
    label = "<stdin>" if args.file == "-" else args.file
    if args.json:
        print(json.dumps({
            "file": label,
            "tokens": rep.tokens,
            "score": rep.score,
            "findings": [vars(f) for f in rep.findings],
        }, ensure_ascii=False, indent=2))
        return 0
    print(f"file:   {label}")
    print(f"tokens: {rep.tokens}")
    print(f"score:  {rep.score}/100")
    if not rep.findings:
        print("(no findings — all clear)")
        return 0
    print("findings:")
    for r in rep.recommendations:
        print(f"  - {r}")
    return 0


def cmd_compress(args) -> int:
    text = _read_input(args.file)
    methods = args.methods.split(",") if args.methods else None
    out = compress(text, methods=methods)
    before, after = estimate_tokens(text), estimate_tokens(out)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"wrote: {args.output}  tokens {before} → {after}  ({_pct(before, after)})")
    else:
        sys.stdout.write(out)
        if not out.endswith("\n"):
            sys.stdout.write("\n")
        print(f"# tokens {before} → {after}  ({_pct(before, after)})", file=sys.stderr)
    return 0


def cmd_budget(args) -> int:
    text = _read_input(args.file)
    t = estimate_tokens(text)
    fits = fits_window(text, args.window, args.ratio)
    label = "<stdin>" if args.file == "-" else args.file
    print(f"file:          {label}")
    print(f"tokens:        {t}")
    print(f"window:        {args.window}")
    print(f"ratio limit:   {args.ratio} → {int(args.window * args.ratio)} tokens")
    print(f"fits 50% rule: {'YES' if fits else 'NO — split required'}")
    return 0


def cmd_methods(args) -> int:
    print(f"{'ID':4} {'kind':10} {'framing':10} title")
    for mid, title, framing, kind in METHODS_TABLE:
        print(f"{mid:4} {kind:10} {framing:10} {title}")
    print(f"\nimplemented as compress: {sorted(SAFE_TRANSFORMS.keys())}")
    return 0


def cmd_format(args) -> int:
    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    rows = format_compare(data)
    print(f"{'format':18} {'chars':>8}")
    for r in rows:
        print(f"{r.format:18} {r.chars:>8}")
    print(f"\nbest: {rows[0].format} ({rows[0].chars} chars)")
    return 0


def _pct(before: int, after: int) -> str:
    if before == 0:
        return "0%"
    return f"-{int((before - after) / before * 100)}%"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kpx", description="Karpathy-Optimization toolkit")
    p.add_argument("--version", action="version", version=f"kpx {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("audit", help="audit a prompt against 30 methods")
    a.add_argument("file", help="path to a text file, or '-' for stdin")
    a.add_argument("--json", action="store_true")
    a.set_defaults(fn=cmd_audit)

    c = sub.add_parser("compress", help="apply safe compressions")
    c.add_argument("file", help="path to a text file, or '-' for stdin")
    c.add_argument("-o", "--output")
    c.add_argument("-m", "--methods", help="comma-separated, e.g. M03,M24,M25")
    c.set_defaults(fn=cmd_compress)

    b = sub.add_parser("budget", help="check 50% context-window rule")
    b.add_argument("file", help="path to a text file, or '-' for stdin")
    b.add_argument("--window", type=int, default=200_000)
    b.add_argument("--ratio", type=float, default=0.5)
    b.set_defaults(fn=cmd_budget)

    m = sub.add_parser("methods", help="list all 30 methods")
    m.set_defaults(fn=cmd_methods)

    f = sub.add_parser("format", help="M15 — compare serialization formats for JSON data")
    f.add_argument("file", help="path to a JSON file")
    f.set_defaults(fn=cmd_format)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
