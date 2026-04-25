# 30 Methods — Karpathy-aligned token optimization

Master reference: see the original [Token_최적화_Karpathy_관점.md](https://github.com/) (in the
upstream harness-check repo). This file is the kpx-internal index showing which methods
are implemented in code, which are surfaced as audit recommendations, and which require
external dependencies.

Karpathy's 8 mental-model framings used as tags:

| Tag | Framing | Source |
|---|---|---|
| F1 | LLM OS | *Intro to LLMs* (2023-11) |
| F2 | Software 3.0 | YC AI Startup School (2025-06) |
| F3 | Context Engineering | X 2025-06-26 (Lütke endorsement) |
| F4 | Animals vs Ghosts | bearblog 2025-10-02 |
| F5 | Verifiability | bearblog 2025-11 |
| F6 | Vibe coding | X 2025-02 + bearblog MenuGen 2025-04 |
| F7 | People spirits | X 2025-06-26 |
| F8 | Pretraining = lossy compression | *State of GPT* (2023-05) |

| ID | Title | Framing | Kind | Notes |
|---|---|---|---|---|
| M01 | Context window = RAM awareness | F1 | audit | `kpx budget` enforces 50% rule |
| M02 | "Just the right info" | F3 | manual | reviewer judgment |
| M03 | Strip pretraining-known facts | F8 | compress | regex |
| M04 | Minimize system prompt | F2 | compress | drops redundant lines |
| M05 | Compress tool/MCP schema | F2+F3 | manual | per-vendor |
| M06 | RAG limited to next-step | F3 | manual | pipeline design |
| M07 | Sliding window + rolling summary | F1+F4 | external | needs LLM call |
| M08 | Few-shot example budget | F5+F2 | audit | flags large example blocks |
| M09 | Output filler ban instruction | F2+F7 | inject | `inject_no_filler()` |
| M10 | Reasoning trace delegation | F1+F5 | audit | suggests reasoning models |
| M11 | Prompt caching | F1 | audit | recommends static prefix |
| M12 | Speculative decoding | F1 | external | inference infra |
| M13 | Tokenizer-aware writing | F2 | manual | needs tiktoken |
| M14 | Code vs natural language | F2 | manual | A/B per task |
| M15 | Serialization format compare | F1+F2 | compare | `kpx format` |
| M16 | Embedding pre-filter | F3 | external | vector DB |
| M17 | Tool calls over context dumps | F1+F3 | manual | architecture |
| M18 | Long-term memory externalize | F4 | external | KV/vector store |
| M19 | Lossy summary | F8 (meta) | compress | extractive heuristic |
| M20 | Verifiability for fewer rounds | F5 | external | structured outputs |
| M21 | Vibe coding workflow | F6 | manual | process |
| M22 | Multi-agent split | F1+F3 | external | orchestrator |
| M23 | Persona consistency | F7 | manual | combine with M11 |
| M24 | Strip polite filler | F2 | compress | regex |
| M25 | Strip duplicated role tags | F2 | compress | regex · fenced/inline code 보존 (B13 fix, R3) |
| M26 | Streaming + early termination | F5 | manual | `stop` sequences |
| M27 | Constrained decoding | F5+F2 | external | outlines/instructor |
| M28 | Quantization | F1 | external | model side |
| M29 | Distillation | F8 | external | training side |
| M30 | Apply order (composite) | all | guide | see README Phases |

## Phases (from upstream master doc)

- **Phase 1 (Day 0–1, ROI ★★★)**: M01 → M11 → M03 → M09 → M24 → M25 → M15 → M23
- **Phase 2 (Week 1–2, structure)**: M04 → M05 → M02 → M08 → M26 → M27 → M21
- **Phase 3 (Month 1, architecture)**: M07 → M10 → M14 → M16 → M19 → M20
- **Phase 4 (Quarter 1, system)**: M06 → M17 → M18 → M22
- **Phase 5 (model side)**: M12 → M13 → M28 → M29
