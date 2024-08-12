import json
from typing import Generator, Any

from bpmn_assistant.config import logger
from bpmn_assistant.core.enums import OutputMode, Provider, MessageRole
from bpmn_assistant.core.llm_provider import LLMProvider
from bpmn_assistant.core.provider_factory import ProviderFactory


class LLMFacade:
    def __init__(
        self,
        provider: Provider,
        api_key: str,
        model: str,
        output_mode: OutputMode = OutputMode.JSON,
    ):
        """
        Initialize the LLM facade with the given provider, API key, model, and output mode.
        Args:
            provider: The provider to use (openai or anthropic)
            api_key: The API key for the provider
            model: The model to use
            output_mode: The output mode (JSON or text)
        """
        self.provider: LLMProvider = ProviderFactory.get_provider(
            provider, api_key, output_mode
        )
        self.model = model
        self.output_mode = output_mode

        if not self.provider.check_model_compatibility(self.model):
            raise ValueError(f"Unsupported model for provider {provider}: {self.model}")

        self.messages = self.provider.get_initial_messages()

    def call(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3
    ) -> str | dict[str, Any]:
        """
        Call the LLM model with the given prompt.
        """
        logger.info(f"Calling LLM: {self.model}")

        response = self.provider.call(
            self.model, prompt, self.messages, max_tokens, temperature
        )

        # Append the response to the message history in case the JSON is invalid and
        # we need to re-run the call
        if self.output_mode == OutputMode.JSON:
            self.provider.add_message(
                self.messages, MessageRole.ASSISTANT, json.dumps(response)
            )

        return response

    def stream(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3
    ) -> Generator[str, None, None]:
        """
        Call the LLM model with the given prompt and stream the response.
        """
        logger.info(f"Calling LLM (streaming): {self.model}")

        return self.provider.stream(
            self.model, prompt, self.messages, max_tokens, temperature
        )
