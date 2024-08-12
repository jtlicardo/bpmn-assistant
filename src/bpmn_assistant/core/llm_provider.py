from abc import ABC, abstractmethod
from typing import Generator, Any

from bpmn_assistant.core.enums import MessageRole


class LLMProvider(ABC):
    @abstractmethod
    def call(
        self,
        model: str,
        prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str | dict[str, Any]:
        pass

    @abstractmethod
    def stream(
        self,
        model: str,
        prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def get_initial_messages(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def add_message(
        self, messages: list[dict[str, str]], role: MessageRole, content: str
    ) -> None:
        pass

    @abstractmethod
    def check_model_compatibility(self, model: str) -> bool:
        pass
