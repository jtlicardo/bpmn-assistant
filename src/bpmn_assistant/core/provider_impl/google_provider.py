import json
from typing import Generator, Any

import google.generativeai as genai  # type: ignore

from bpmn_assistant.config import logger
from bpmn_assistant.core.enums import OutputMode, GoogleModels, MessageRole
from bpmn_assistant.core.llm_provider import LLMProvider


class GoogleProvider(LLMProvider):
    def __init__(self, api_key: str, output_mode: OutputMode = OutputMode.JSON):
        self.output_mode = output_mode
        genai.configure(api_key=api_key)

    def call(
        self,
        model: str,
        prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str | dict[str, Any]:
        """
        Implementation of the Google Gemini API call.
        """
        model_instance = genai.GenerativeModel(model)
        chat = model_instance.start_chat(history=messages)

        response_mime_type = (
            "application/json" if self.output_mode == OutputMode.JSON else "text/plain"
        )

        response = chat.send_message(
            content=prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                response_mime_type=response_mime_type,
            ),
        )

        return self._process_response(response.text)

    def stream(
        self,
        model: str,
        prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Generator[str, None, None]:
        """
        Implementation of the Google Gemini API stream.
        """
        model_instance = genai.GenerativeModel(model)
        chat = model_instance.start_chat(history=messages)

        response = chat.send_message(
            content=prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
            stream=True,
        )

        for chunk in response:
            yield chunk.text

    def get_initial_messages(self) -> list[dict[str, str]]:
        return []

    def add_message(
        self, messages: list[dict[str, str]], role: MessageRole, content: str
    ) -> None:
        message_role = "model" if role == MessageRole.ASSISTANT else "user"
        messages.append({"role": message_role, "parts": content})

    def check_model_compatibility(self, model: str) -> bool:
        return model in [m.value for m in GoogleModels]

    def _process_response(self, raw_output: str) -> str | dict[str, Any]:
        """
        Process the raw output from the model. Returns the appropriate response based on the output mode.
        If the output mode is JSON, the raw output is parsed and returned as a dict.
        If the output mode is text, the raw output is returned as is.
        """
        if self.output_mode == OutputMode.JSON:
            try:
                result = json.loads(raw_output)

                if not isinstance(result, dict):
                    raise ValueError(f"Invalid JSON response from Google: {result}")

                return result
            except json.decoder.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                logger.error(f"Raw output: {raw_output}")
                raise Exception("Invalid JSON response from Google") from e
        elif self.output_mode == OutputMode.TEXT:
            return raw_output
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")
