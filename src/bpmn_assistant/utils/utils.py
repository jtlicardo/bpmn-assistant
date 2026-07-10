import os

from dotenv import load_dotenv

from bpmn_assistant.core import LLMFacade, MessageItem, MessageImage
from bpmn_assistant.core.enums import (
    AnthropicModels,
    BPMNElementType,
    EventDefinitionType,
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
    else:
        raise Exception("Invalid model")

    if not api_key:
        raise Exception(f"API key not found for provider {provider}")

    return LLMFacade(
        provider,
        api_key,
        model,
        output_mode=output_mode,
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
    else:
        # Local Docker mode - check environment variables
        load_dotenv(override=True)
        openai_present = bool(os.getenv("OPENAI_API_KEY"))
        anthropic_present = bool(os.getenv("ANTHROPIC_API_KEY"))

    return {
        "openai": openai_present,
        "anthropic": anthropic_present,
    }


def is_openai_model(model: str) -> bool:
    return model in [model.value for model in OpenAIModels]


def is_anthropic_model(model: str) -> bool:
    return model in [model.value for model in AnthropicModels]


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
