import json

from bpmn_assistant.core.enums import OutputMode, Provider
from bpmn_assistant.core.llm_provider import LLMProvider, StreamingResponse
from bpmn_assistant.core.provider_factory import ProviderFactory
from bpmn_assistant.config import logger


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
    ) -> str | dict:
        """
        Call the LLM model with the given prompt.
        """
        logger.info(f"Calling LLM: {self.model}")

        self.messages.append({"role": "user", "content": prompt})

        response = self.provider.call(self.model, self.messages, max_tokens, temperature)

        # Append the response to the message history in case the JSON is invalid and
        # we need to re-run the call
        if self.output_mode == OutputMode.JSON:
            self.messages.append({"role": "assistant", "content": json.dumps(response)})

        return response

    def stream(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3
    ) -> StreamingResponse:
        """
        Call the LLM model with the given prompt and stream the response.
        """
        logger.info(f"Calling LLM (streaming): {self.model}")

        self.messages.append({"role": "user", "content": prompt})

        return self.provider.stream(self.model, self.messages, max_tokens, temperature)