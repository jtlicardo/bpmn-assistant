from importlib import resources

from bpmn_assistant.config import logger
from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.utils import prepare_prompt, message_history_to_string


def define_change_request(
    llm_facade: LLMFacade, process: list[dict], message_history: list[MessageItem]
) -> str:
    """
    Defines the change to be made in the BPMN process based on the message history.
    Args:
        llm_facade: The LLM facade object
        process: The BPMN process
        message_history: The message history
    Returns:
        str: The change request
    """

    prompt_template = resources.read_text(
        "bpmn_assistant.prompts", "define_change_request.txt"
    )

    prompt = prepare_prompt(
        prompt_template,
        process=str(process),
        message_history=message_history_to_string(message_history),
    )

    json_object = llm_facade.call(prompt, max_tokens=100, temperature=0.4)

    # TODO: validate the response, retry until it's valid

    logger.info(f"Change request: {json_object['change_request']}")

    return json_object["change_request"]
