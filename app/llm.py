"""The language model behind any OpenAI-compatible endpoint.

Settings come from the environment only: LLM_BASE_URL, LLM_API_KEY and LLM_MODEL. No temperature is
sent, because some endpoints refuse it. The caller validates the reply, because not every endpoint
enforces the schema.
"""

import json
import os
import threading
from collections import Counter

from openai import OpenAI

MAX_TOKENS = 8000

# Tokens used by this process, so a run can say what it cost instead of guessing.
usage: Counter = Counter()
_usage_lock = threading.Lock()


class ModelNotConfigured(RuntimeError):
    """The model settings are missing, so nothing new can be extracted."""


def model_name() -> str:
    return os.environ.get("LLM_MODEL") or ""


def complete_json(system: str, user: str, schema_name: str, schema: dict) -> dict:
    api_key = os.environ.get("LLM_API_KEY")
    model = model_name()
    if not api_key or not model:
        raise ModelNotConfigured(
            "LLM_API_KEY and LLM_MODEL are not set, so this source cannot be extracted. Put the model"
            " settings in .env and run with: uv run --env-file .env python -m app.ingest"
        )
    client = OpenAI(api_key=api_key, base_url=os.environ.get("LLM_BASE_URL") or None)
    response = client.chat.completions.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
    )
    with _usage_lock:
        usage["input"] += response.usage.prompt_tokens
        usage["output"] += response.usage.completion_tokens
        usage["calls"] += 1
    choice = response.choices[0]
    if choice.finish_reason not in ("stop", "end_turn"):
        raise RuntimeError(f"The model stopped early: finish_reason={choice.finish_reason}")
    return json.loads(choice.message.content)
