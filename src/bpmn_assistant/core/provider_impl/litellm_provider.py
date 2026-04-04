import json
import os
from typing import Any, Generator

from litellm import completion
from pydantic import BaseModel

from bpmn_assistant.config import logger
from bpmn_assistant.core.enums.models import (
    AnthropicModels,
    FireworksAIModels,
    GoogleModels,
    OpenAIModels,
)
from bpmn_assistant.core.enums.output_modes import OutputMode
from bpmn_assistant.core.json_parser import parse_json_loose
from bpmn_assistant.core.llm_provider import LLMProvider


class LiteLLMProvider(LLMProvider):
    def __init__(self, api_key: str, output_mode: OutputMode = OutputMode.JSON):
        self.output_mode = output_mode
        os.environ["ANTHROPIC_API_KEY"] = api_key
        os.environ["FIREWORKS_AI_API_KEY"] = api_key
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key

    def _is_openai_model(self, model: str) -> bool:
        """Check if the given model is an OpenAI model."""
        return model in [m.value for m in OpenAIModels]

    def _validate_vision_support(
        self, model: str, messages: list[dict[str, Any]]
    ) -> None:
        """
        Validate that only vision-supported models receive image content.
        Raises ValueError if images are sent to non-OpenAI models.
        """
        has_images = any(
            isinstance(msg.get("content"), list)
            and any(item.get("type") == "image_url" for item in msg.get("content", []))
            for msg in messages
        )

        if has_images and not self._is_openai_model(model):
            raise ValueError(
                f"Vision input is only supported for OpenAI models. "
                f"Model '{model}' does not support image inputs."
            )

    def _process_response(self, raw_output: str) -> str | dict[str, Any]:
        """
        Process the raw output from the model. Returns the appropriate response based on the output mode.
        If the output mode is JSON, the raw output is parsed and returned as a dict.
        If the output mode is text, the raw output is returned as is.
        """
        if self.output_mode == OutputMode.JSON:
            try:
                result = json.loads(raw_output)
            except json.decoder.JSONDecodeError as e:
                logger.debug(
                    f"Strict JSON parsing failed for model response. "
                    f"Trying loose parser. Error: {e}"
                )
                try:
                    result = parse_json_loose(raw_output)
                except json.decoder.JSONDecodeError as loose_error:
                    logger.error(f"JSONDecodeError: {loose_error}")
                    logger.error(f"Raw output: {raw_output}")
                    raise Exception("Invalid JSON response from LLM") from loose_error

            if not isinstance(result, dict):
                raise ValueError(f"Invalid JSON response from LLM: {result}")

            return result
        elif self.output_mode == OutputMode.TEXT:
            return raw_output
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")

    def call(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        structured_output: type[BaseModel] | None = None,
    ) -> str | dict[str, Any]:
        self._validate_vision_support(model, messages)

        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if structured_output is not None or self.output_mode == OutputMode.JSON:
            params["response_format"] = {"type": "json_object"}

        params["max_tokens"] = max_tokens

        # GPT-5 models only support temperature=1
        if model == OpenAIModels.GPT_5_2.value:
            params["temperature"] = 1
        else:
            params["temperature"] = temperature

        logger.debug(
            f"Sending prompt (model={model}): {json.dumps(messages, indent=2)}"
        )

        response = completion(**params)

        if not response.choices:
            logger.error(f"Emtpy response from model: {response.choices}")
            raise Exception("Empty response from model")

        raw_output = response.choices[0].message.content

        if raw_output is None:
            logger.error(f"Model returned None content: {response}")
            raise Exception("Model returned empty content")

        return self._process_response(raw_output)

    def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Generator[str, None, None]:
        self._validate_vision_support(model, messages)

        # GPT-5 models only support temperature=1
        if model == OpenAIModels.GPT_5_2.value:
            temperature = 1

        response = completion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        for chunk in response:
            fragment = chunk.choices[0].delta.content or ""
            if fragment:
                yield fragment

    def get_initial_messages(self) -> list[dict[str, str]]:
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
        return (
            model in [m.value for m in FireworksAIModels]
            or model in [m.value for m in OpenAIModels]
            or model in [m.value for m in GoogleModels]
            or model in [m.value for m in AnthropicModels]
        )
