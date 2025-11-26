import json
from typing import Any, Generator

from pydantic import BaseModel

from bpmn_assistant.config import logger
from bpmn_assistant.core.enums import MessageRole, OutputMode, Provider
from bpmn_assistant.core.llm_provider import LLMProvider
from bpmn_assistant.core.provider_factory import ProviderFactory
from bpmn_assistant.core.schemas import MessageImage


class LLMFacade:
    def __init__(
        self,
        provider: Provider,
        api_key: str,
        model: str,
        output_mode: OutputMode = OutputMode.JSON,
        base_url: str | None = None,
    ):
        """
        Initialize the LLM facade with the given provider, API key, model, and output mode.
        Args:
            provider: The provider to use (openai or anthropic)
            api_key: The API key for the provider
            model: The model to use
            output_mode: The output mode (JSON or text)
            base_url: Optional custom base URL for API requests (e.g., for self-hosted models)
        """
        self.provider: LLMProvider = ProviderFactory.get_provider(
            provider, api_key, output_mode, base_url
        )
        self.model = model
        self.output_mode = output_mode

        if not self.provider.check_model_compatibility(self.model):
            raise ValueError(f"Unsupported model for provider {provider}: {self.model}")

        self.messages = self.provider.get_initial_messages()

    def _append_user_message(
        self,
        prompt: str,
        images: list[MessageImage] | None = None,
    ) -> None:
        """Append a user message to the conversation, handling optional images."""
        if images:
            content = [{"type": "text", "text": prompt}]
            for image in images:
                content.append(
                    {"type": "image_url", "image_url": {"url": image.preview}}
                )
            message = {"role": MessageRole.USER.value, "content": content}
        else:
            message = {"role": MessageRole.USER.value, "content": prompt}

        self.messages.append(message)

    def call(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        structured_output: BaseModel | None = None,
        images: list[MessageImage] | None = None,
    ) -> str | dict[str, Any]:
        """
        Call the LLM model with the given prompt.
        Args:
            prompt: The text prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            structured_output: Optional structured output schema
            images: Optional list of images to attach to the user message
        """
        logger.info(f"Calling LLM: {self.model}")

        self._append_user_message(prompt, images)

        response = self.provider.call(
            self.model,
            self.messages,
            max_tokens,
            temperature,
            structured_output,
        )

        if self.output_mode == OutputMode.JSON:
            if not isinstance(response, dict):
                raise ValueError(f"Provider returned non-dict in JSON mode: {response}")
            self.messages.append(
                {"role": MessageRole.ASSISTANT.value, "content": json.dumps(response)}
            )

        return response

    def stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        images: list[MessageImage] | None = None,
    ) -> Generator[str, None, None]:
        """
        Call the LLM model and stream the response.

        Args:
            prompt: The text prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            images: Optional list of images to attach to the user message
        """
        logger.info(f"Calling LLM (streaming): {self.model}")

        self._append_user_message(prompt, images)

        return self.provider.stream(self.model, self.messages, max_tokens, temperature)
