from importlib import resources

from bpmn_assistant.config import logger
from bpmn_assistant.core import LLMFacade
from bpmn_assistant.utils import prepare_prompt


def determine_intent(llm_facade: LLMFacade, message_history: list) -> dict:
    """
    Determine the intent of the user based on the message history.
    The possible intents are "modify" and "talk".
    Args:
        llm_facade: The LLM facade
        message_history: The message history
    Returns:
        dict: The response containing the intent
    """
    prompt_template = resources.read_text(
        "bpmn_assistant.prompts", "determine_intent.txt"
    )

    prompt = prepare_prompt(
        prompt_template,
        message_history=str(message_history),
    )

    json_object, _ = llm_facade.call(prompt, max_tokens=50, temperature=0.3)

    logger.info(f"Intent: {json_object}")

    # TODO: validate the response and retry if necessary

    return json_object
