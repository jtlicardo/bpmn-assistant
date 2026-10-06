from enum import Enum


class OpenAIModels(Enum):
    GPT_6_1_SOL = "gpt-6.1-sol"
    GPT_6_LUNA = "gpt-6-luna"


class AnthropicModels(Enum):
    OPUS_5_5 = "claude-opus-5-5"
    SONNET_5_5 = "claude-sonnet-5-5"
