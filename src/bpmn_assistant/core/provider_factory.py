from .enums import Provider
from .llm_provider import LLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


class ProviderFactory:
    @staticmethod
    def get_provider(
        provider: str, api_key: str, output_mode: str = "json", streaming: bool = False
    ) -> LLMProvider:
        if provider == Provider.OPENAI.value:
            return OpenAIProvider(api_key, output_mode, streaming)
        elif provider == Provider.ANTHROPIC.value:
            return AnthropicProvider(api_key, output_mode, streaming)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
