from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def call(self, model: str, messages: list, max_tokens: int, temperature: float):
        pass

    @abstractmethod
    def get_initial_messages(self):
        pass

    @abstractmethod
    def check_model_compatibility(self, model: str) -> bool:
        pass
