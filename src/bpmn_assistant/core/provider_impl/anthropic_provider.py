import json
from typing import Any, Generator

from anthropic import Anthropic
from anthropic.types import TextBlock
from pydantic import BaseModel

from bpmn_assistant.config import logger
from bpmn_assistant.core.enums import AnthropicModels, OutputMode
from bpmn_assistant.core.llm_provider import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, output_mode: OutputMode = OutputMode.JSON):
        self.output_mode = output_mode
        self.client = Anthropic(api_key=api_key)

    def call(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        structured_output: BaseModel | None = None,
    ) -> str | dict[str, Any]:
        """
        Implementation of the Anthropic API call.
        """
        logger.debug(
            f"Sending prompt (model={model}): {json.dumps(messages, indent=2)}"
        )

        if self.output_mode == OutputMode.JSON:
            # We add "{" to constrain the model to output a JSON object
            messages.append({"role": "assistant", "content": "{"})

            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are a helpful assistant designed to output JSON.",
                messages=messages,  # type: ignore[arg-type]
            )

            content = response.content[0]

            if not isinstance(content, TextBlock):
                raise ValueError(f"Invalid response from Anthropic: {content}")

            # Remove the "{" we added from the messages
            messages.pop()

            raw_output = content.text

            # Add "{" back to the raw output to make it a valid JSON object
            raw_output = "{" + raw_output

            return self._process_response(raw_output)
        else:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,  # type: ignore[arg-type]
            )

            content = response.content[0]

            if not isinstance(content, TextBlock):
                raise ValueError(f"Invalid response from Anthropic: {content}")

            raw_output = content.text

            return self._process_response(raw_output)

    def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Generator[str, None, None]:
        """
        Implementation of the Anthropic API stream.
        """
        response = self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,  # type: ignore[arg-type]
        )

        with response as stream:
            for text in stream.text_stream:
                yield text

    def get_initial_messages(self) -> list[dict[str, str]]:
        return []

    def check_model_compatibility(self, model: str) -> bool:
        return model in [m.value for m in AnthropicModels]

    def _process_response(self, raw_output: str) -> str | dict[str, Any]:
        """
        Process the raw output from the model. Returns the appropriate response based on the output mode.
        If the output mode is JSON, the raw output is parsed and returned as a JSON object.
        If the output mode is text, the raw output is returned as is.
        """
        if self.output_mode == OutputMode.JSON:
            try:
                result = json.loads(raw_output)

                if not isinstance(result, dict):
                    raise ValueError(f"Invalid JSON response from Anthropic: {result}")

                return result
            except json.decoder.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                logger.error(f"Raw output: {raw_output}")
                raise Exception("Invalid JSON response from Anthropic") from e
        elif self.output_mode == OutputMode.TEXT:
            return raw_output
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")
