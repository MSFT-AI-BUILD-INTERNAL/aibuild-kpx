"""Static / offline analysis of kpx behavior (no API calls).

These analyzers measure properties that are independent of the downstream
LLM, making them deterministic, free, and ideal for CI:

- :mod:`code_preservation` — does V1..V5 keep code blocks, identifiers,
  signposts, and technical terms intact? Pure string/AST inspection.
- :mod:`realistic_prompts` — corpus of 15 real-world coding system prompts
  modeled after popular tools (Copilot/Cursor/Aider/plain Python).
"""
