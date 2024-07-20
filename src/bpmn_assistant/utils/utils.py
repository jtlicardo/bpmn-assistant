import os

from dotenv import load_dotenv

from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.core.enums import Provider, OpenAIModels, AnthropicModels, OutputMode


def prepare_prompt(prompt_template, **kwargs):
    """
    Replace the placeholders in the prompt template with the given values.

    Args:
        prompt_template (str): The prompt template.
        **kwargs: Keyword arguments where keys are variable names (without '::')
                  and values are the replacement strings.

    Returns:
        str: The prompt
    """

    # TODO: maybe it would be good to check if any passed variable is not in the prompt_template

    prompt = prompt_template

    # Replace each variable with its corresponding value
    for variable, value in kwargs.items():
        prompt = prompt.replace(f"::{variable}", value)

    return prompt


def get_llm_facade(
        model: str, output_mode: OutputMode = OutputMode.JSON
) -> LLMFacade:
    """
    Get the LLM facade based on the model type
    Args:
        model: The model to use
        output_mode: The output mode for the LLM response (JSON or text)
    Returns:
        LLMFacade: The LLM facade
    """
    load_dotenv(override=True)

    if is_openai_model(model):
        api_key = os.getenv("OPENAI_API_KEY")
        provider = Provider.OPENAI
    elif is_anthropic_model(model):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        provider = Provider.ANTHROPIC
    else:
        raise Exception("Invalid model")

    return LLMFacade(
        provider,
        api_key,
        model,
        output_mode=output_mode,
    )


def get_provider_based_on_model(model: str) -> Provider:
    if is_openai_model(model):
        return Provider.OPENAI
    elif is_anthropic_model(model):
        return Provider.ANTHROPIC
    else:
        raise ValueError("Invalid model")


def get_available_providers() -> dict:
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    openai_present = openai_api_key is not None and len(openai_api_key) > 0
    anthropic_present = anthropic_api_key is not None and len(anthropic_api_key) > 0

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
