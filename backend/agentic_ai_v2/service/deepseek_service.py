"""DeepSeek client and structured-output helpers for analysis v2."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

load_dotenv()

DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_BASE_URL = os.getenv(
    "DEEPSEEK_BASE_URL",
    "https://api.deepseek.com",
)

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


@lru_cache(maxsize=1)
def _get_deepseek_client() -> OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("Missing DEEPSEEK_API_KEY in environment.")
    return OpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
    )


def _messages_with_json_schema(
    messages: list[dict[str, str]],
    output_model: type[BaseModel],
) -> list[dict[str, str]]:
    schema = json.dumps(
        output_model.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    instruction = (
        "Return only one valid JSON object matching the following JSON Schema. "
        "Do not wrap the JSON in Markdown or add any text outside the JSON object.\n"
        f"JSON Schema: {schema}"
    )
    output = [dict(message) for message in messages]
    for message in output:
        if message.get("role") == "system":
            message["content"] = f"{message.get('content', '')}\n\n{instruction}"
            break
    else:
        output.insert(0, {"role": "system", "content": instruction})
    return output


def create_structured_completion(
    *,
    messages: list[dict[str, str]],
    output_model: type[StructuredOutput],
    max_tokens: int,
    temperature: float = 0.1,
) -> StructuredOutput:
    """Call DeepSeek JSON mode and validate its content with Pydantic.

    V4 defaults to thinking mode. Analysis v2 disables it to retain the low
    latency and deterministic behavior expected from the previous mini model.
    One retry covers DeepSeek JSON mode's documented occasional empty output.
    """
    client = _get_deepseek_client()
    structured_messages = _messages_with_json_schema(messages, output_model)
    last_error: Exception | None = None

    for _attempt in range(2):
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=structured_messages,
            response_format={"type": "json_object"},
            extra_body={"thinking": {"type": "disabled"}},
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            last_error = ValueError("DeepSeek returned empty JSON content")
            continue
        try:
            return output_model.model_validate_json(content)
        except (ValidationError, ValueError) as exc:
            last_error = exc

    raise ValueError("DeepSeek returned invalid structured output") from last_error
