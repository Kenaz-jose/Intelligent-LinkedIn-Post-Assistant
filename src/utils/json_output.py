import json
import re

_FENCE = re.compile(r"^```(?:json)?|```$", re.MULTILINE)
_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(raw: str) -> dict:
    """
    Pull a JSON object out of a raw LLM reply.

    Handles the three things models do even when told not to:
      1. Wrapping the JSON in ```json fences.
      2. Adding a sentence before or after it.
      3. Adding trailing whitespace or newlines.

    Raises ValueError if no JSON object is present, so the caller
    can retry rather than silently continuing with bad data.
    """
    cleaned = _FENCE.sub("", raw).strip()

    match = _OBJECT.search(cleaned)
    if not match:
        raise ValueError(f"No JSON object found in model output: {cleaned[:200]}")

    return json.loads(match.group(0))