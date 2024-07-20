from abc import ABC, abstractmethod

from anthropic import MessageStreamManager
from openai import Stream
from openai.types.chat import ChatCompletionChunk

type StreamingResponse = Stream[ChatCompletionChunk] | MessageStreamManager

class LLMProvider(ABC):
    @abstractmethod
    def call(self, model: str, messages: list, max_tokens: int, temperature: float) -> str | dict:
        pass

    @abstractmethod
    def stream(self, model: str, messages: list, max_tokens: int, temperature: float) -> StreamingResponse:
        pass

    @abstractmethod
    def get_initial_messages(self) -> list[dict]:
        pass

    @abstractmethod
    def check_model_compatibility(self, model: str) -> bool:
        pass
