from importlib import resources

from bpmn_assistant.config import logger
from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.utils import prepare_prompt, message_history_to_string


def define_change_request(llm_facade: LLMFacade, message_history: list[MessageItem]) -> str:
    """
    Defines the change to be made in the BPMN process based on the message history.
    Args:
        llm_facade: The LLM facade object
        message_history: The message history
    Returns:
        str: The change request
    """

    # TODO: we should probably also receive the process here, so we can reason about it

    prompt_template = resources.read_text(
        "bpmn_assistant.prompts", "define_change_request.txt"
    )

    prompt = prepare_prompt(
        prompt_template,
        message_history=message_history_to_string(message_history),
    )

    json_object, _ = llm_facade.call(prompt, max_tokens=100, temperature=0.5)

    # TODO: validate the response, retry until it's valid

    logger.info(f"Change request: {json_object['change_request']}")

    return json_object["change_request"]
