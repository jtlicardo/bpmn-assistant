from enum import Enum


class OpenAIModels(Enum):
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_4 = "gpt-4-turbo"
    GPT_4O = "gpt-4o"


class AnthropicModels(Enum):
    HAIKU = "claude-3-haiku-20240307"
    SONNET = "claude-3-sonnet-20240229"
    OPUS = "claude-3-opus-20240229"
    SONNET_3_5 = "claude-3-5-sonnet-20240620"
