import json
import os
import re
import mimetypes
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
    def __init__(self, api_key: str, output_mode: OutputMode = OutputMode.JSON):
        self.output_mode = output_mode
        os.environ["FIREWORKS_AI_API_KEY"] = api_key
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key

    def _format_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        formatted: list[dict[str, Any]] = []
        for message in messages:
            if message.get("image_url"):
                mime, _ = mimetypes.guess_type(message["image_url"])
                parts = []
                if message.get("content"):
                    parts.append({"type": "text", "text": message["content"]})
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": message["image_url"],
                            **({"format": mime} if mime else {}),
                        },
                    }
                )
                formatted.append({"role": message["role"], "content": parts})
            else:
                formatted.append({"role": message["role"], "content": message.get("content", "")})
        return formatted

    def call(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
        structured_output: BaseModel | None = None,
    ) -> str | dict[str, Any]:
        params: dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
        }

        if structured_output is not None or self.output_mode == OutputMode.JSON:
            params["response_format"] = {"type": "json_object"}

        if model != OpenAIModels.O4_MINI.value:
            params["max_tokens"] = max_tokens
            params["temperature"] = temperature

        response = completion(**params)

        if not response.choices:
            logger.error(f"Emtpy response from model: {response.choices}")
            raise Exception("Empty response from model")

        raw_output = response.choices[0].message.content

        if model in [
            FireworksAIModels.DEEPSEEK_R1.value,
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
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
    ) -> Generator[str, None, None]:
        response = completion(
            model=model,
            messages=self._format_messages(messages),
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

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

    def get_initial_messages(self) -> list[dict[str, Any]]:
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
