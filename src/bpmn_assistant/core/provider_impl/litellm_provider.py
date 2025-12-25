import json
import os
import re
from typing import Any, Generator

from litellm import completion
from pydantic import BaseModel

from bpmn_assistant.config import logger
from bpmn_assistant.core.enums.models import (
    FireworksAIModels,
    GoogleModels,
    OpenAIModels,
)
from bpmn_assistant.core.enums.output_modes import OutputMode
from bpmn_assistant.core.llm_provider import LLMProvider


class LiteLLMProvider(LLMProvider):
    def __init__(self, api_key: str, output_mode: OutputMode = OutputMode.JSON, base_url: str | None = None):
        self.output_mode = output_mode
        self.base_url = base_url
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

    def _resolve_model_name(self, model: str) -> str:
        # Use custom model name if base_url is set and OPENAI_MODEL_NAME env var is provided
        # Prefix with "openai/" so litellm knows to use OpenAI provider format
        actual_model = model
        if self.base_url and self._is_openai_model(model):
            custom_model_name = os.getenv("OPENAI_MODEL_NAME")
            if custom_model_name:
                actual_model = custom_model_name
            # Prefix with "openai/" for custom base_url to tell litellm which provider format to use
            if not actual_model.startswith("openai/"):
                actual_model = f"openai/{actual_model}"
        return actual_model

    def call(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        structured_output: BaseModel | None = None,
    ) -> str | dict[str, Any]:
        self._validate_vision_support(model, messages)

        actual_model = self._resolve_model_name(model)

        params: dict[str, Any] = {
            "model": actual_model,
            "messages": messages,
        }

        if structured_output is not None or self.output_mode == OutputMode.JSON:
            params["response_format"] = {"type": "json_object"}

        params["max_tokens"] = max_tokens

        # GPT-5 models only support temperature=1
        if model in [OpenAIModels.GPT_5_1.value, OpenAIModels.GPT_5_MINI.value]:
            params["temperature"] = 1
        else:
            params["temperature"] = temperature

        # Use custom base_url if provided (for self-hosted models)
        if self.base_url and self._is_openai_model(model):
            params["api_base"] = self.base_url

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

        if model in [
            FireworksAIModels.QWEN_3_235B.value,
        ]:
            # Extract thinking phase and clean output
            think_pattern = r"<think>(.*?)</think>"
            think_match = re.search(think_pattern, raw_output, re.DOTALL)

            if think_match:
                thinking = think_match.group(1).strip()
                logger.info(f"Model thinking phase: {thinking}")
                raw_output = re.sub(
                    think_pattern, "", raw_output, flags=re.DOTALL
                ).strip()

        return self._process_response(raw_output)

    def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Generator[str, None, None]:
        self._validate_vision_support(model, messages)

        actual_model = self._resolve_model_name(model)

        # GPT-5 models only support temperature=1
        if model in [OpenAIModels.GPT_5_1.value, OpenAIModels.GPT_5_MINI.value]:
            temperature = 1

        stream_params = {
            "model": actual_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        # Use custom base_url if provided (for self-hosted models)
        if self.base_url and self._is_openai_model(model):
            stream_params["api_base"] = self.base_url

        response = completion(**stream_params)

        open_tag, close_tag = "<think>", "</think>"
        inside_think = False
        thought_parts: list[str] = []
        buffer = ""
        first_payload_sent = False

        try:
            for chunk in response:
                fragment = chunk.choices[0].delta.content or ""
                if not fragment:
                    continue

                buffer += fragment
                while buffer:
                    if inside_think:
                        end_idx = buffer.find(close_tag)
                        if end_idx == -1:
                            thought_parts.append(buffer)
                            buffer = ""
                        else:
                            thought_parts.append(buffer[:end_idx])
                            buffer = buffer[end_idx + len(close_tag) :]
                            inside_think = False
                    else:
                        start_idx = buffer.find(open_tag)
                        if start_idx == -1:
                            payload = buffer
                            buffer = ""
                        else:
                            payload = buffer[:start_idx]
                            buffer = buffer[start_idx + len(open_tag) :]
                            inside_think = True

                        if payload:
                            if not first_payload_sent:
                                payload = payload.lstrip("\n")
                                if not payload:
                                    continue
                                first_payload_sent = True
                            yield payload
        finally:
            thought = "".join(thought_parts).strip()
            if thought:
                logger.info(f"Model thinking phase: {thought}")

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

                if not isinstance(result, dict):
                    raise ValueError(f"Invalid JSON response from LLM: {result}")

                return result
            except json.decoder.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                logger.error(f"Raw output: {raw_output}")
                raise Exception("Invalid JSON response from LLM") from e
        elif self.output_mode == OutputMode.TEXT:
            return raw_output
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")
