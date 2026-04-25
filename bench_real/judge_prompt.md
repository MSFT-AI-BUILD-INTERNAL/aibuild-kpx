# LLM-as-Judge prompt (kpx bench-real, plan v2 §7)

You are evaluating a single LLM response on **four axes**, each scored 0–25.
Sum is 0–100. Return **JSON only** — no prose, no markdown.

## Axes
1. **correctness** — Does the response satisfy the user's request?
2. **completeness** — Are all required pieces present (no truncation, no missing fields)?
3. **faithfulness** — Does the response avoid claims not supported by the input?
4. **conciseness** — Is it free of preamble, postamble, and filler?

## Inputs

### System prompt
{{SYSTEM}}

### User message
{{USER}}

### Model response
{{RESPONSE}}

## Output (JSON, no other text)
```
{"correctness": <0-25>, "completeness": <0-25>, "faithfulness": <0-25>, "conciseness": <0-25>, "note": "<≤30 chars>"}
```
