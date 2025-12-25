import json
import traceback

from bpmn_assistant.config import logger
from bpmn_assistant.core import LLMFacade, MessageItem, MessageImage
from bpmn_assistant.prompts import PromptTemplateProcessor
from bpmn_assistant.services.process_editing import (
    BpmnEditingService,
    define_change_request,
)
from bpmn_assistant.utils import message_history_to_string

from .validate_bpmn import validate_bpmn


class BpmnModelingService:
    """
    Service for creating and editing BPMN processes.
    """

    def __init__(self):
        self.prompt_processor = PromptTemplateProcessor()

    def create_bpmn(
        self,
        llm_facade: LLMFacade,
        message_history: list[MessageItem],
        images: list[MessageImage] | None = None,
        max_retries: int = 3,
    ) -> list:
        """
        Create a BPMN process.
        Args:
            llm_facade: The LLMFacade object.
            message_history: The message history.
            images: Optional list of images to attach to the request.
            max_retries: The maximum number of retries in case of failure.
        Returns:
            list: The BPMN process.
        """

        prompt = self.prompt_processor.render_template(
            "create_bpmn.jinja2",
            message_history=message_history_to_string(message_history),
        )

        attempts = 0
        last_error: Exception | None = None

        while attempts < max_retries:
            attempts += 1
            try:
                response = llm_facade.call(prompt, max_tokens=3000, images=images)
                logger.debug(f"LLM response:\n{json.dumps(response, indent=2)}")
                process = response["process"]
                validate_bpmn(process)
                logger.debug(
                    f"Generated BPMN process:\n{json.dumps(process, indent=2)}"
                )
                return process  # Return the process if it's valid
            except (ValueError, Exception) as e:
                last_error = e
                logger.warning(
                    f"Error (attempt {attempts}): {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                prompt = f"Error: {str(e)}. Try again."

        message = "Max number of retries reached. Could not create the BPMN process."
        if last_error:
            message += f" Last error from provider: {last_error}"
        raise ValueError(message)

    def edit_bpmn(
        self,
        llm_facade: LLMFacade,
        text_llm_facade: LLMFacade,
        process: list[dict],
        message_history: list[MessageItem],
        images: list[MessageImage] | None = None,
    ) -> list:
        change_request = define_change_request(
            text_llm_facade, process, message_history, images=images
        )

        bpmn_editor_service = BpmnEditingService(llm_facade, process, change_request)

        return bpmn_editor_service.edit_bpmn()
