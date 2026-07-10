from enum import Enum


class OpenAIModels(Enum):
    GPT_5_6_SOL = "gpt-5.6-sol"
    GPT_5_6_LUNA = "gpt-5.6-luna"


class AnthropicModels(Enum):
    OPUS_4_8 = "claude-opus-4-8"
    SONNET_5 = "claude-sonnet-5"
