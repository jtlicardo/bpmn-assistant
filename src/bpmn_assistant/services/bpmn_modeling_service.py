import traceback
from importlib import resources

from bpmn_assistant.config import logger
from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.core.enums import BPMNElementType
from bpmn_assistant.services.process_editing import (
    BpmnEditorService,
    define_change_request,
)
from bpmn_assistant.utils import prepare_prompt, message_history_to_string


class BpmnModelingService:
    """
    Service for creating and editing BPMN processes.
    """

    def create_bpmn(
        self,
        llm_facade: LLMFacade,
        message_history: list[MessageItem],
        max_retries: int = 3,
    ) -> list:
        """
        Create a BPMN process.
        Args:
            llm_facade: The LLMFacade object.
            message_history: The message history.
            max_retries: The maximum number of retries in case of failure.
        Returns:
            list: The BPMN process.
        """
        prompt_template = resources.read_text(
            "bpmn_assistant.prompts", "create_bpmn.txt"
        )

        prompt = prepare_prompt(
            prompt_template, message_history=message_history_to_string(message_history)
        )

        response = llm_facade.call(prompt)

        attempts = 0

        while attempts < max_retries:
            attempts += 1

            try:
                self._validate_bpmn(response["process"])
                return response["process"]  # Return the process if it's valid
            except Exception as e:
                logger.warning(
                    f"Validation error (attempt {attempts}): {str(e)}\n"
                    f"Invalid process: {response['process']}\n"
                    f"Traceback: {traceback.format_exc()}"
                )

                new_prompt = f"Error: {str(e)}. Try again."

                response = llm_facade.call(new_prompt)

        raise Exception(
            "Max number of retries reached. Could not create the BPMN process."
        )

    def edit_bpmn(
        self,
        llm_facade: LLMFacade,
        process: list[dict],
        message_history: list[MessageItem],
    ) -> list:
        change_request = define_change_request(llm_facade, process, message_history)

        bpmn_editor_service = BpmnEditorService(llm_facade, process, change_request)

        return bpmn_editor_service.edit_bpmn()

    def _validate_bpmn(self, process: list) -> None:
        """
        Validate the BPMN process.
        Args:
            process: The BPMN process in JSON format.
        Raises:
            Exception: If the BPMN process is invalid.
        """
        try:
            for element in process:
                self._validate_element(element)

                if element["type"] == "exclusiveGateway":
                    for branch in element["branches"]:
                        self._validate_bpmn(branch["path"])
                if element["type"] == "parallelGateway":
                    for branch in element["branches"]:
                        self._validate_bpmn(branch)
        except Exception as e:
            raise e

    def _validate_element(self, element: dict) -> None:
        """
        Validate the BPMN element.
        Args:
            element: The BPMN element in JSON format.
        Raises:
            Exception: If the BPMN element is invalid.
        """
        if "id" not in element:
            raise Exception(f"Element is missing an ID: {element}")
        elif "type" not in element:
            raise Exception(f"Element is missing a type: {element}")

        supported_elements = [e.value for e in BPMNElementType]

        if element["type"] not in supported_elements:
            raise Exception(
                f"Unsupported element type: {element['type']}. Supported types: {supported_elements}"
            )

        if element["type"] in ["task", "userTask", "serviceTask"]:
            if "label" not in element:
                raise Exception(f"Task element is missing a label: {element}")

        elif element["type"] == "exclusiveGateway":
            if "label" not in element:
                raise Exception(f"Exclusive gateway is missing a label: {element}")
            if "branches" not in element or not isinstance(element["branches"], list):
                raise Exception(
                    f"Exclusive gateway is missing or has invalid 'branches': {element}"
                )
            for branch in element["branches"]:
                if "condition" not in branch or "path" not in branch:
                    raise Exception(f"Invalid branch in exclusive gateway: {branch}")

        elif element["type"] == "parallelGateway":
            if "branches" not in element or not isinstance(element["branches"], list):
                raise Exception(
                    f"Parallel gateway is missing or has invalid 'branches': {element}"
                )
