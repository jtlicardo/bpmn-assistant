from enum import Enum


class OpenAIModels(Enum):
    GPT_5_2 = "gpt-5.2-2025-12-11"
    GPT_4_1 = "gpt-4.1"

class AnthropicModels(Enum):
    SONNET_4_5 = "claude-sonnet-4-5-20250929"
    OPUS_4_6 = "claude-opus-4-6"


class GoogleModels(Enum):
    GEMINI_3_FLASH = "gemini/gemini-3-flash-preview"
    GEMINI_3_1_PRO = "gemini/gemini-3.1-pro-preview"


class FireworksAIModels(Enum):
    KIMI_K2P5 = "fireworks_ai/kimi-k2p5"
