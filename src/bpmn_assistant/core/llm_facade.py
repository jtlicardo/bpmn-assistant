from openai import Stream
from anthropic import MessageStreamManager
from openai.types.chat import ChatCompletionChunk

from bpmn_assistant.core.llm_provider import LLMProvider
from bpmn_assistant.core.provider_factory import ProviderFactory
from bpmn_assistant.config import logger


class LLMFacade:
    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        output_mode: str = "json",
        streaming: bool = False,
    ):
        """
        Initialize the LLM facade with the given provider, API key, model, and output mode.
        Args:
            provider: The provider to use (openai or anthropic)
            api_key: The API key for the provider
            model: The model to use
            output_mode: The output mode (json or text)
            streaming: Whether to use streaming or not
        """
        self.provider: LLMProvider = ProviderFactory.get_provider(
            provider, api_key, output_mode, streaming
        )
        self.model = model
        self.output_mode = output_mode
        self.streaming = streaming

        if not self.provider.check_model_compatibility(self.model):
            raise ValueError(f"Unsupported model for provider {provider}: {self.model}")

        self.messages = self.provider.get_initial_messages()

    def call(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3
    ) -> (
        tuple[dict, list]
        | tuple[str, list]
        | Stream[ChatCompletionChunk]
        | MessageStreamManager
    ):
        """
        Call the LLM model with the given prompt.
        Returns the response from the model and the message history.
        If the output mode is JSON, the response is returned as a JSON object.
        If the output mode is text, the response is returned as a string.
        If streaming is enabled, the response is returned as a stream.
        """
        logger.info(f"Calling LLM: {self.model}")

        self.messages.append({"role": "user", "content": prompt})

        return self.provider.call(self.model, self.messages, max_tokens, temperature)
