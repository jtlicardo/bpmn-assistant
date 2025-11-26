import os

from dotenv import load_dotenv

from bpmn_assistant.core import LLMFacade, MessageItem, MessageImage
from bpmn_assistant.core.enums import (
    AnthropicModels,
    BPMNElementType,
    EventDefinitionType,
    FireworksAIModels,
    GoogleModels,
    OpenAIModels,
    OutputMode,
    Provider,
)


def get_llm_facade(model: str, output_mode: OutputMode = OutputMode.JSON, api_keys: dict[str, str] | None = None) -> LLMFacade:
    """
    Get the LLM facade based on the model type
    Args:
        model: The model to use
        output_mode: The output mode for the LLM response (JSON or text)
        api_keys: Optional dictionary of API keys from user (takes precedence over env vars)
    Returns:
        LLMFacade: The LLM facade
    Raises:
        Exception: If the model is invalid or if the required API key is not set
    """
    load_dotenv(override=True)

    if api_keys is None:
        api_keys = {}

    if is_openai_model(model):
        api_key = api_keys.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        provider = Provider.OPENAI
    elif is_anthropic_model(model):
        api_key = api_keys.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
        provider = Provider.ANTHROPIC
    elif is_google_model(model):
        api_key = api_keys.get("google_api_key") or os.getenv("GEMINI_API_KEY")
        provider = Provider.GOOGLE
    elif is_fireworks_ai_model(model):
        api_key = api_keys.get("fireworks_api_key") or os.getenv("FIREWORKS_AI_API_KEY")
        provider = Provider.FIREWORKS_AI
    else:
        raise Exception("Invalid model")

    if not api_key:
        raise Exception(f"API key not found for provider {provider}")

    # Read custom base_url from env for self-hosted models
    base_url = None
    if is_openai_model(model):
        base_url = os.getenv("OPENAI_BASE_URL")

    return LLMFacade(
        provider,
        api_key,
        model,
        output_mode=output_mode,
        base_url=base_url,
    )


def get_available_providers(api_keys: dict[str, str] | None = None) -> dict:
    """
    Get available providers from user-provided keys or environment variables.
    Args:
        api_keys: Optional dictionary of API keys from user (takes precedence over env vars)
    Returns:
        dict: Dictionary with provider availability status
    """
    if api_keys is None:
        api_keys = {}

    # If user provided any keys (BYOK mode), only check those
    # Otherwise, check environment variables (local Docker mode)
    if len(api_keys) > 0:
        # BYOK mode - only check user-provided keys
        openai_present = bool(api_keys.get("openai_api_key"))
        anthropic_present = bool(api_keys.get("anthropic_api_key"))
        google_present = bool(api_keys.get("google_api_key"))
        fireworks_ai_present = bool(api_keys.get("fireworks_api_key"))
    else:
        # Local Docker mode - check environment variables
        load_dotenv(override=True)
        openai_present = bool(os.getenv("OPENAI_API_KEY"))
        anthropic_present = bool(os.getenv("ANTHROPIC_API_KEY"))
        google_present = bool(os.getenv("GEMINI_API_KEY"))
        fireworks_ai_present = bool(os.getenv("FIREWORKS_AI_API_KEY"))

    result = {
        "openai": openai_present,
        "anthropic": anthropic_present,
        "google": google_present,
        "fireworks_ai": fireworks_ai_present,
    }

    # Include custom model name if OPENAI_BASE_URL and OPENAI_MODEL_NAME are set
    if len(api_keys) == 0:  # Only in local Docker mode
        openai_base_url = os.getenv("OPENAI_BASE_URL")
        openai_model_name = os.getenv("OPENAI_MODEL_NAME")
        if openai_base_url and openai_model_name:
            result["openai_model_name"] = openai_model_name

    return result


def replace_reasoning_model(model: str) -> str:
    """
    Replaces reasoning models with more lightweight models.
    """
    if model in [
        FireworksAIModels.QWEN_3_235B.value,
    ]:
        return FireworksAIModels.DEEPSEEK_V3_1.value
    return model


def is_openai_model(model: str) -> bool:
    return model in [model.value for model in OpenAIModels]


def is_anthropic_model(model: str) -> bool:
    return model in [model.value for model in AnthropicModels]


def is_google_model(model: str) -> bool:
    return model in [model.value for model in GoogleModels]


def is_fireworks_ai_model(model: str) -> bool:
    return model in [model.value for model in FireworksAIModels]


def message_history_to_string(message_history: list[MessageItem]) -> str:
    """
    Convert a message history list into a formatted string.
    """
    return "\n".join(
        f"{message.role.capitalize()}: {message.content}" for message in message_history
    )


def extract_images_from_message_history(
    message_history: list[MessageItem],
) -> list[MessageImage]:
    """
    Extract all images from all messages in the message history.
    Returns a flat list of all images.
    """
    images = []
    for message in message_history:
        if message.images:
            images.extend(message.images)
    return images


def get_supported_bpmn_elements() -> str:
    """
    Generate a human-readable list of supported BPMN elements.
    Returns:
        str: A formatted string describing all supported BPMN elements
    """
    # Group elements by category
    tasks = []
    gateways = []
    events = []

    for element in BPMNElementType:
        name = element.value
        # Convert camelCase to Title Case with spaces
        readable_name = ''.join([' ' + c if c.isupper() else c for c in name]).strip().title()

        if 'task' in name.lower():
            tasks.append(readable_name)
        elif 'gateway' in name.lower():
            gateways.append(readable_name)
        elif 'event' in name.lower():
            events.append(readable_name)

    # Build the description
    parts = []

    if events:
        parts.append(f"Events: {', '.join(events)}")
    if tasks:
        parts.append(f"Tasks: {', '.join(tasks)}")
    if gateways:
        parts.append(f"Gateways: {', '.join(gateways)}")

    # Add event definitions
    event_defs = [ed.value.replace('EventDefinition', ' Event').title()
                  for ed in EventDefinitionType if ed.value is not None]
    if event_defs:
        parts.append(f"Event Definitions: {', '.join(event_defs)}")

    parts.append("Sequence Flows")

    return "; ".join(parts)
