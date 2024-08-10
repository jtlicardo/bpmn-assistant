from enum import Enum


class OpenAIModels(Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o-2024-08-06"


class AnthropicModels(Enum):
    HAIKU = "claude-3-haiku-20240307"
    SONNET_3_5 = "claude-3-5-sonnet-20240620"
