from importlib import resources

from bpmn_assistant.core import LLMFacade
from bpmn_assistant.core.exceptions import ProcessException
from bpmn_assistant.services.process_editing import (
    delete_element,
    redirect_flow,
    add_element,
    move_element,
    update_element,
)
from bpmn_assistant.utils import prepare_prompt
from bpmn_assistant.config import logger


class BpmnEditorService:
    def __init__(self, llm_facade: LLMFacade, process: list, change_request: str):
        self.llm_facade = llm_facade
        self.process = process
        self.change_request = change_request

    def edit_bpmn(self) -> list:
        """
        Edit a BPMN process based on a change request.
        Returns:
            The updated BPMN process
        """
        updated_process = self._apply_initial_edit()
        updated_process = self._apply_intermediate_edits(updated_process)

        return updated_process

    def _apply_initial_edit(self) -> list:
        response = self._get_initial_edit_proposal()
        updated_process = self._attempt_process_update_with_retries(
            self.process, response
        )
        return updated_process

    def _apply_intermediate_edits(
        self,
        updated_process: list,
        max_num_of_iterations: int = 7,
    ) -> list:
        for _ in range(max_num_of_iterations):
            response = self._get_intermediate_edit_proposal(updated_process)

            if "stop" in response:
                logger.info("Edit process stopped.")
                return updated_process
            else:
                # The 'response' is the edit proposal (function and arguments)
                updated_process = self._attempt_process_update_with_retries(
                    updated_process, response
                )

        raise Exception("Max number of iterations reached. Process not fully edited.")

    def _attempt_process_update_with_retries(
        self, process: list, edit_proposal: dict, max_retries: int = 3
    ) -> list:
        attempts = 0

        while attempts < max_retries:
            attempts += 1

            try:
                updated_process = self._update_process(process, edit_proposal)
                return updated_process  # Update was successful
            except ProcessException as e:
                error_message = str(e)
                logger.warning(
                    f"Validation error (attempt {attempts}): {error_message}"
                )

                new_prompt = f"Error: {error_message}. Try again. Change request: {self.change_request}"

                edit_proposal, _ = self.llm_facade.call(new_prompt)
                logger.info(f"New edit proposal: {edit_proposal}")

                if "stop" in edit_proposal:
                    return process

        raise Exception("Max number of retries reached. Process not fully edited.")

    def _update_process(self, process: list, edit_proposal: dict) -> list:
        """
        Update the process based on the edit proposal.
        Args:
            process: The BPMN process to be edited
            edit_proposal: The edit proposal from the LLM (function and args)
        Returns:
            The updated process
        """
        edit_functions = {
            "delete_element": delete_element,
            "redirect_flow": redirect_flow,
            "add_element": add_element,
            "move_element": move_element,
            "update_element": update_element,
        }

        function_to_call = edit_proposal["function"]
        args = edit_proposal["arguments"]

        res = edit_functions[function_to_call](process, **args)
        return res["process"]  # Return the updated process

    def _get_initial_edit_proposal(self, max_retries: int = 3) -> dict:
        prompt_template = resources.read_text("bpmn_assistant.prompts", "edit_bpmn.txt")

        prompt = prepare_prompt(
            prompt_template,
            process=str(self.process),
            change_request=self.change_request,
        )

        response, _ = self.llm_facade.call(prompt)
        logger.info(f"Initial edit proposal: {response}")

        attempts = 0

        while attempts < max_retries:
            attempts += 1

            try:
                self._validate_llm_response(response)
                return response  # Return the response if it's valid
            except ValueError as e:
                error_message = str(e)
                logger.warning(
                    f"Validation error (attempt {attempts}): {error_message}"
                )

                new_prompt = f"Editing error: {error_message}. Please provide a new edit proposal."

                # We need the call the LLM again
                response, _ = self.llm_facade.call(new_prompt)
                logger.info(f"New initial edit proposal: {response}")

        raise Exception("Max number of retries reached.")

    def _get_intermediate_edit_proposal(
        self, updated_process: list, max_retries: int = 3
    ) -> dict:
        """
        Get an intermediate edit proposal from the LLM.
        Args:
            updated_process: The updated BPMN process
            max_retries: The maximum number of retries to perform if the response is invalid
        Returns:
            The intermediate edit proposal (function and arguments)
        """
        prompt_template = resources.read_text(
            "bpmn_assistant.prompts", "edit_bpmn_intermediate_step.txt"
        )

        prompt = prepare_prompt(
            prompt_template,
            process=str(updated_process),
        )

        response, _ = self.llm_facade.call(prompt)
        logger.info(f"Intermediate edit proposal: {response}")

        attempts = 0

        while attempts < max_retries:
            attempts += 1

            try:
                self._validate_llm_response(response, is_first_edit=False)
                return response  # Return the response if it's valid
            except ValueError as e:
                error_message = str(e)
                logger.warning(
                    f"Validation error (attempt {attempts}): {error_message}"
                )

                new_prompt = f"Editing error: {error_message}. Please provide a new edit proposal."

                # We need the call the LLM again
                response, _ = self.llm_facade.call(new_prompt)
                logger.info(f"New intermediate edit proposal: {response}")

        raise Exception("Max number of retries reached.")

    def _validate_llm_response(
        self, response: dict, is_first_edit: bool = True
    ) -> bool:

        if not is_first_edit and "stop" in response:
            return True

        # The dict should have 'function' and 'arguments' keys
        if "function" not in response or "arguments" not in response:
            msg = "Function call should contain 'function' and 'arguments' keys."
            logger.error(msg)
            raise ValueError(msg)

        function_to_call = response["function"]
        args = response["arguments"]

        if function_to_call == "delete_element":
            if "element_id" not in args:
                self._log_raise("Arguments should contain 'element_id' key.")
            elif len(args) > 1:
                self._log_raise("Arguments should contain only 'element_id' key.")
        elif function_to_call == "redirect_flow":
            if "element_id" not in args or "next_id" not in args:
                self._log_raise(
                    "Arguments should contain 'element_id' and 'next_id' keys."
                )
            elif len(args) > 2:
                self._log_raise(
                    "Arguments should contain only 'element_id' and 'next_id' keys."
                )
        elif function_to_call == "add_element":
            if "element" not in args:
                self._log_raise("Arguments should contain 'element' key.")
            elif "before_id" in args and "after_id" in args:
                self._log_raise(
                    "Only one of 'before_id' and 'after_id' should be provided."
                )
            elif "before_id" not in args and "after_id" not in args:
                self._log_raise("Either 'before_id' or 'after_id' should be provided.")
            elif len(args) > 2:
                self._log_raise(
                    "Arguments should contain only 'element' and either 'before_id' or 'after_id' keys."
                )
        elif function_to_call == "move_element":
            if "element_id" not in args:
                self._log_raise("Arguments should contain 'element_id' key.")
            elif "before_id" in args and "after_id" in args:
                self._log_raise(
                    "Only one of 'before_id' and 'after_id' should be provided."
                )
            elif "before_id" not in args and "after_id" not in args:
                self._log_raise("Either 'before_id' or 'after_id' should be provided.")
            elif len(args) > 2:
                self._log_raise(
                    "Arguments should contain only 'element_id' and either 'before_id' or 'after_id' keys."
                )
        elif function_to_call == "update_element":
            if "new_element" not in args:
                self._log_raise("Arguments should contain 'new_element' key.")
            elif len(args) > 1:
                self._log_raise("Arguments should contain only 'new_element' key.")
        else:
            self._log_raise(f"Function '{function_to_call}' not found.")

        return True

    def _log_raise(self, msg: str) -> None:
        logger.error(msg)
        raise ValueError(msg)
