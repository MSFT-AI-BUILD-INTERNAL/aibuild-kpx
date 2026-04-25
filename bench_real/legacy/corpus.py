"""Synthetic prompt corpus for kpx benchmarking.

30 prompts across 6 categories × 5 styles = 30 base prompts.
Each prompt is intentionally crafted to exercise different optimization paths.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Prompt:
    id: str
    category: str
    style: str
    text: str


def _coding_polite() -> str:
    return (
        "You are a helpful assistant.\n"
        "Please write a Python function that sorts a list. Thank you so much in advance.\n"
        "I'd like you to also add type hints. Would you please add docstrings as well?"
    )


def _coding_verbose() -> str:
    return (
        "You are an AI assistant. As you probably know, Python is a high-level "
        "interpreted dynamic language. JavaScript is an object-oriented scripting "
        "language. HTTP stands for HyperText Transfer Protocol. Now, write a function "
        "that fetches a URL and parses JSON. Please respond carefully and provide a response."
    )


def _coding_with_code_block() -> str:
    return (
        "Refactor this snippet:\n"
        "```python\n"
        "# Python is a high-level interpreted language. (do not modify this comment)\n"
        "def f(x):\n"
        "    return x * 2\n"
        "```\n"
        "Please make it polymorphic. Thank you."
    )


def _coding_role_tags() -> str:
    return (
        "<|system|>You are a coder.<|im_end|>\n"
        "[INST] Write a CLI tool. [/INST]\n"
        "### Instruction: Use argparse.\n"
        "### Response:"
    )


def _coding_clean() -> str:
    return "Refactor this function for readability. Use early returns where natural."


def _docs_polite() -> str:
    return (
        "You are a helpful technical writer. Please summarize this design doc. "
        "Thank you in advance. I'd like you to use bullet points."
    )


def _docs_long() -> str:
    body = "This paragraph explains the architecture. " * 50
    return f"# Design Doc\n\n## Overview\n\n{body}\n\n## Details\n\n{body}\n"


def _docs_filler() -> str:
    return (
        "You are an AI language model. Please respond carefully and provide a response. "
        "Do your best. Now summarize the following document. " + ("Lorem ipsum dolor. " * 30)
    )


def _docs_with_signposts() -> str:
    return (
        "Summarize the spec. Please note that section 3 is critical. "
        "Please refer to Appendix A for terminology. Please see Figure 2 for the diagram."
    )


def _docs_clean() -> str:
    return "Summarize this RFC into a 5-bullet TL;DR for engineers."


def _data_json() -> str:
    return (
        "[{\"id\":1,\"name\":\"alice\",\"role\":\"admin\"},"
        "{\"id\":2,\"name\":\"bob\",\"role\":\"user\"},"
        "{\"id\":3,\"name\":\"carol\",\"role\":\"user\"}]"
    )


def _data_yaml_dump() -> str:
    return (
        "items:\n  - id: 1\n    name: alice\n    role: admin\n"
        "  - id: 2\n    name: bob\n    role: user\n"
        "  - id: 3\n    name: carol\n    role: user\n"
    )


def _data_with_polite_wrap() -> str:
    return (
        "You are a data analyst. Please look at this data and tell me anomalies. Thank you.\n\n"
        + _data_yaml_dump()
    )


def _data_repeated_logs() -> str:
    return ("ERROR: connection timeout\n" * 100) + "WARN: retry exhausted"


def _data_clean() -> str:
    return "Aggregate the rows by role and report counts."


def _agentic_long_history() -> str:
    turns = []
    for i in range(15):
        turns.append(f"USER: question {i}")
        turns.append(f"ASSISTANT: answer {i}. " + ("Lorem ipsum dolor sit amet. " * 10))
    return "\n".join(turns)


def _agentic_few_shot() -> str:
    examples = "\n\n".join([f"Example: input{i} -> output{i}" for i in range(8)])
    return (
        "You are a classifier. Examples:\n\n" + examples + "\n\nClassify: input_X"
    )


def _agentic_cot() -> str:
    return (
        "You are a math tutor. Let's think step by step. Solve: integral of x^2 dx. "
        "Show CoT and chain-of-thought reasoning."
    )


def _agentic_tool_dump() -> str:
    schema = ",".join([f"\"col_{i}\":\"VARCHAR(255)\"" for i in range(50)])
    return (
        "You are a SQL agent. The full schema is: {" + schema + "}. "
        "Given the user wants top 10 customers by revenue, write the query."
    )


def _agentic_clean() -> str:
    return "Plan a 3-step retrieval-then-generate workflow for the question above."


def _safety_polite() -> str:
    return (
        "You are a content moderator. Please flag any unsafe content. Thank you. "
        "If you don't mind, also categorize by severity."
    )


def _safety_verbose() -> str:
    return (
        "You are an AI assistant. Please respond carefully. As you probably know, "
        "content safety is critical. Please provide a response with severity 1-5."
    )


def _safety_role_tags() -> str:
    return "<|system|>moderator<|im_end|>\n[INST] check this text [/INST]"


def _safety_signposts() -> str:
    return (
        "Moderate this snippet. Please note false positives are costly. "
        "Please refer to policy v3.2."
    )


def _safety_clean() -> str:
    return "Flag policy violations with category and severity 1-5."


def _multilingual_korean() -> str:
    return (
        "당신은 친절한 도우미입니다. 다음 문서를 요약해 주세요. 감사합니다. "
        + ("이 문장은 본문입니다. " * 40)
    )


def _multilingual_emoji() -> str:
    return "🎉 You are a helpful assistant 🎊. Please write a poem 🚀. Thank you 💖."


def _multilingual_url_heavy() -> str:
    return (
        "Please summarize: https://example.com/docs/" + ("a" * 300)
        + " and https://other.example.com/" + ("b" * 200)
    )


def _multilingual_mixed() -> str:
    return (
        "<|system|>You are 친절한 도우미.<|im_end|>\n"
        "Please write 코드. Thank you so much. "
        "Python is a high-level interpreted language. 감사합니다."
    )


def _multilingual_clean() -> str:
    return "이 RFC를 5줄 TL;DR로 요약해."


_BUILDERS = [
    ("coding", "polite", _coding_polite),
    ("coding", "verbose", _coding_verbose),
    ("coding", "code_block", _coding_with_code_block),
    ("coding", "role_tags", _coding_role_tags),
    ("coding", "clean", _coding_clean),
    ("docs", "polite", _docs_polite),
    ("docs", "long", _docs_long),
    ("docs", "filler", _docs_filler),
    ("docs", "signposts", _docs_with_signposts),
    ("docs", "clean", _docs_clean),
    ("data", "json", _data_json),
    ("data", "yaml", _data_yaml_dump),
    ("data", "polite_wrap", _data_with_polite_wrap),
    ("data", "repeated_logs", _data_repeated_logs),
    ("data", "clean", _data_clean),
    ("agentic", "long_history", _agentic_long_history),
    ("agentic", "few_shot", _agentic_few_shot),
    ("agentic", "cot", _agentic_cot),
    ("agentic", "tool_dump", _agentic_tool_dump),
    ("agentic", "clean", _agentic_clean),
    ("safety", "polite", _safety_polite),
    ("safety", "verbose", _safety_verbose),
    ("safety", "role_tags", _safety_role_tags),
    ("safety", "signposts", _safety_signposts),
    ("safety", "clean", _safety_clean),
    ("multilingual", "korean", _multilingual_korean),
    ("multilingual", "emoji", _multilingual_emoji),
    ("multilingual", "url_heavy", _multilingual_url_heavy),
    ("multilingual", "mixed", _multilingual_mixed),
    ("multilingual", "clean", _multilingual_clean),
]


def all_prompts() -> list[Prompt]:
    return [
        Prompt(id=f"P{i+1:02d}", category=cat, style=style, text=fn())
        for i, (cat, style, fn) in enumerate(_BUILDERS)
    ]
