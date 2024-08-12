from importlib import resources
from typing import Optional, Generator

from bpmn_assistant.core import MessageItem
from bpmn_assistant.core.enums import OutputMode
from bpmn_assistant.utils import (
    prepare_prompt,
    get_llm_facade,
    message_history_to_string,
)


class ConversationalService:

    def __init__(self, model: str):
        self.llm_facade = get_llm_facade(model, output_mode=OutputMode.TEXT)

    def respond_to_query(
        self, message_history: list[MessageItem], process: Optional[list]
    ) -> Generator:
        """
        Respond to the user query based on the message history and BPMN process.
        Args:
            llm_facade: The LLM facade object (needs to have 'text' output mode)
            message_history: The message history
            process: The BPMN process
        Returns:
            Generator: A generator that yields the response
        """
        if not process:
            prompt_template = resources.read_text(
                "bpmn_assistant.prompts", "respond_to_query_no_process.txt"
            )

            prompt = prepare_prompt(
                prompt_template,
                message_history=message_history_to_string(message_history),
            )
        else:
            prompt_template = resources.read_text(
                "bpmn_assistant.prompts", "respond_to_query.txt"
            )

            prompt = prepare_prompt(
                prompt_template,
                message_history=message_history_to_string(message_history),
                process=str(process),
            )

        yield from self.llm_facade.stream(prompt, max_tokens=500, temperature=0.5)

    def make_final_comment(
        self, message_history: list[MessageItem], process: list
    ) -> Generator:
        """
        Make a final comment after the process is created/edited.
        Args:
            message_history: The message history
            process: The BPMN process in JSON format
        Returns:
            Generator: A generator that yields the final comment
        """
        # TODO: prepare_prompt should take care of reading the template
        prompt_template = resources.read_text(
            "bpmn_assistant.prompts", "make_final_comment.txt"
        )

        prompt = prepare_prompt(
            prompt_template,
            message_history=message_history_to_string(message_history),
            process=str(process),
        )

        yield from self.llm_facade.stream(prompt, max_tokens=200, temperature=0.5)
