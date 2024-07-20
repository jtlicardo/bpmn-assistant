import json

from openai import OpenAI

from bpmn_assistant.config import logger
from .enums import OpenAIModels, OutputMode
from .llm_provider import LLMProvider, StreamingResponse


class OpenAIProvider(LLMProvider):
    def __init__(
        self, api_key: str, output_mode: OutputMode = OutputMode.JSON
    ):
        self.api_key = api_key
        self.output_mode = output_mode
        self.client = OpenAI(api_key=self.api_key)

    def call(self, model: str, messages: list, max_tokens: int, temperature: float) -> str | dict:
        """
        Implementation of the OpenAI API call.
        """
        response_format = {"type": "json_object"} if self.output_mode == OutputMode.JSON else {"type": "text"}

        response = self.client.chat.completions.create(
            model=model,
            response_format=response_format,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        raw_output = response.choices[0].message.content

        return self._process_response(raw_output)

    def stream(self, model: str, messages: list, max_tokens: int, temperature: float) -> StreamingResponse:
        """
        Implementation of the OpenAI API stream.
        """
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

    def get_initial_messages(self) -> list[dict]:
        return (
            [
                {
                    "role": "system",
                    "content": "You are a helpful assistant designed to output JSON.",
                }
            ]
            if self.output_mode == OutputMode.JSON
            else []
        )

    def check_model_compatibility(self, model: str) -> bool:
        return model in [m.value for m in OpenAIModels]

    def _process_response(self, raw_output: str) -> str | dict:
        """
        Process the raw output from the model. Returns the appropriate response based on the output mode.
        If the output mode is JSON, the raw output is parsed and returned as a dict.
        If the output mode is text, the raw output is returned as is.
        """
        if self.output_mode == OutputMode.JSON:
            try:
                return json.loads(raw_output)
            except json.decoder.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                logger.error(f"Raw output: {raw_output}")
                raise Exception("Invalid JSON response from OpenAI") from e
        elif self.output_mode == OutputMode.TEXT:
            return raw_output
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")
