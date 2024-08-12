import os

from dotenv import load_dotenv

from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.core.enums import (
    Provider,
    OpenAIModels,
    AnthropicModels,
    OutputMode,
    GoogleModels,
)


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
    prompt = prompt_template

    # Extract variables from the template
    template_parts = prompt_template.split("::")
    template_variables = [part.split()[0] for part in template_parts[1:]]

    # Check for unused variables
    passed_variables = set(kwargs.keys())
    template_variable_set = set(template_variables)
    unused_variables = passed_variables - template_variable_set

    if unused_variables:
        raise ValueError(
            f"The following variables were passed but not found in the template: {', '.join(unused_variables)}"
        )

    # Replace each variable with its corresponding value
    for variable, value in kwargs.items():
        placeholder = f"::{variable}"
        if placeholder not in prompt:
            raise ValueError(f"Variable '{variable}' not found in the prompt template.")
        prompt = prompt.replace(placeholder, value)

    return prompt


def get_llm_facade(model: str, output_mode: OutputMode = OutputMode.JSON) -> LLMFacade:
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
    elif is_google_model(model):
        api_key = os.getenv("GOOGLE_API_KEY")
        provider = Provider.GOOGLE
    else:
        raise Exception("Invalid model")

    return LLMFacade(
        provider,
        api_key,
        model,
        output_mode=output_mode,
    )


def get_available_providers() -> dict:
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    openai_present = openai_api_key is not None and len(openai_api_key) > 0
    anthropic_present = anthropic_api_key is not None and len(anthropic_api_key) > 0
    google_present = google_api_key is not None and len(google_api_key) > 0

    return {
        "openai": openai_present,
        "anthropic": anthropic_present,
        "google": google_present,
    }


def is_openai_model(model: str) -> bool:
    return model in [model.value for model in OpenAIModels]


def is_anthropic_model(model: str) -> bool:
    return model in [model.value for model in AnthropicModels]


def is_google_model(model: str) -> bool:
    return model in [model.value for model in GoogleModels]


def message_history_to_string(message_history: list[MessageItem]) -> str:
    """
    Convert a message history list into a formatted string.
    """
    return "\n".join(
        f"{message.role.capitalize()}: {message.content}" for message in message_history
    )
