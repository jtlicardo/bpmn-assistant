import json

from anthropic import Anthropic

from bpmn_assistant.config import logger
from .enums import AnthropicModels, OutputMode
from .llm_provider import LLMProvider, StreamingResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, output_mode: OutputMode = OutputMode.JSON):
        self.api_key = api_key
        self.output_mode = output_mode
        self.client = Anthropic(api_key=self.api_key)

    def call(self, model: str, messages: list, max_tokens: int, temperature: float) -> str | dict:
        """
        Implementation of the Anthropic API call.
        """
        if self.output_mode == OutputMode.JSON:
            # We add "{" to constrain the model to output a JSON object
            messages.append({"role": "assistant", "content": "{"})

            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are a helpful assistant designed to output JSON.",
                messages=messages,
            )

            # Remove the "{" we added from the messages
            messages.pop()

            raw_output = response.content[0].text # type: ignore[union-attr]

            # Add "{" back to the raw output to make it a valid JSON object
            raw_output = "{" + raw_output

            return self._process_response(raw_output)
        else:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )

            raw_output = response.content[0].text # type: ignore[union-attr]

            return self._process_response(raw_output)

    def stream(self, model: str, messages: list, max_tokens: int, temperature: float) -> StreamingResponse:
        """
        Implementation of the Anthropic API stream.
        """
        return self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )

    def get_initial_messages(self) -> list[dict]:
        return []

    def check_model_compatibility(self, model: str) -> bool:
        return model in [m.value for m in AnthropicModels]

    def _process_response(self, raw_output: str) -> str | dict:
        """
        Process the raw output from the model. Returns the appropriate response based on the output mode.
        If the output mode is JSON, the raw output is parsed and returned as a JSON object.
        If the output mode is text, the raw output is returned as is.
        """
        if self.output_mode == OutputMode.JSON:
            try:
                return json.loads(raw_output)
            except json.decoder.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                logger.error(f"Raw output: {raw_output}")
                raise Exception("Invalid JSON response from Anthropic") from e
        elif self.output_mode == OutputMode.TEXT:
            return raw_output
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")
