# Contributing to kpx

Thanks for considering a contribution!

## Scope
kpx covers **prompt-side** LLM token optimization. Shell-output filtering belongs to
[`rtk`](https://github.com/rtk-ai/rtk). PRs that overlap with rtk's surface (filtering
git/cargo/pytest output) will likely be closed.

## Development setup

```bash
git clone <your-fork-url>
cd kpx
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Adding a new method

1. Locate the method ID (`M01`–`M30`) in [docs/METHODS.md](docs/METHODS.md).
2. If the transform is **static and safe** (no LLM call, idempotent on already-clean
   text), implement it in `kpx/methods.py` and register in `SAFE_TRANSFORMS`.
3. If it requires an external LLM / vector DB / vendor SDK, surface it as an
   **audit recommendation** in `kpx/audit.py` and document the optional dep.
4. Add at least one positive and one negative test in `tests/`.
5. Update `CHANGELOG.md` under `## [Unreleased]`.

## PR checklist
- [ ] `pytest -q` green
- [ ] No new required runtime deps (optional deps go behind `extras_require`)
- [ ] Method ID cited in commit message and PR title (e.g. `feat(M11): prompt cache adapter`)
- [ ] Docs updated if user-facing behavior changes

## Code style
- Pure stdlib for the core. PyYAML and similar are optional.
- Type hints encouraged but not enforced.
- Keep `kpx audit` self-applying: `kpx audit README.md` should not regress in score.
