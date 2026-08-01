import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pydantic import BaseModel, Field

from agentic_ai_v2.service.deepseek_service import (
    DEEPSEEK_MODEL,
    _messages_with_json_schema,
    create_structured_completion,
)


class ExampleOutput(BaseModel):
    score: float = Field(ge=0, le=1)
    analysis: str = Field(min_length=1)


def _response(content):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


class DeepSeekServiceTests(unittest.TestCase):
    def test_json_schema_instruction_is_added_without_mutating_messages(self):
        messages = [{"role": "user", "content": "Analyze FPT"}]

        output = _messages_with_json_schema(messages, ExampleOutput)

        self.assertEqual(messages, [{"role": "user", "content": "Analyze FPT"}])
        self.assertEqual(output[0]["role"], "system")
        self.assertIn("JSON Schema", output[0]["content"])
        self.assertIn('"score"', output[0]["content"])

    @patch("agentic_ai_v2.service.deepseek_service._get_deepseek_client")
    def test_structured_completion_uses_v4_flash_json_mode(self, get_client):
        create = Mock(return_value=_response('{"score":0.75,"analysis":"Tich cuc"}'))
        get_client.return_value.chat.completions.create = create

        result = create_structured_completion(
            messages=[{"role": "user", "content": "Analyze"}],
            output_model=ExampleOutput,
            max_tokens=500,
        )

        self.assertEqual(result.score, 0.75)
        self.assertEqual(result.analysis, "Tich cuc")
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["model"], DEEPSEEK_MODEL)
        self.assertEqual(kwargs["response_format"], {"type": "json_object"})
        self.assertEqual(
            kwargs["extra_body"],
            {"thinking": {"type": "disabled"}},
        )

    @patch("agentic_ai_v2.service.deepseek_service._get_deepseek_client")
    def test_empty_first_response_is_retried(self, get_client):
        create = Mock(
            side_effect=[
                _response(""),
                _response('{"score":0.5,"analysis":"Trung lap"}'),
            ]
        )
        get_client.return_value.chat.completions.create = create

        result = create_structured_completion(
            messages=[{"role": "user", "content": "Analyze"}],
            output_model=ExampleOutput,
            max_tokens=500,
        )

        self.assertEqual(result.score, 0.5)
        self.assertEqual(create.call_count, 2)


if __name__ == "__main__":
    unittest.main()
