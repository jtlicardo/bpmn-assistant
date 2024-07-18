from importlib import resources
from typing import Optional, Generator

from anthropic import MessageStreamManager
from openai import Stream
from openai.types.chat import ChatCompletionChunk

from bpmn_assistant.core.enums import Provider
from bpmn_assistant.utils import (
    prepare_prompt,
    get_provider_based_on_model,
    get_llm_facade,
)


class ConversationalService:

    def __init__(self, model: str):
        self.provider = get_provider_based_on_model(model)
        self.llm_facade = get_llm_facade(model, output_mode="text", streaming=True)

    def respond_to_query(
        self, message_history: list, process: Optional[list]
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
                message_history=str(message_history),
            )
        else:
            prompt_template = resources.read_text(
                "bpmn_assistant.prompts", "respond_to_query.txt"
            )

            prompt = prepare_prompt(
                prompt_template,
                message_history=str(message_history),
                process=str(process),
            )

        response, _ = self.llm_facade.call(prompt, max_tokens=500, temperature=0.5)

        yield from self._process_streaming_response(response)

    def make_final_comment(self, message_history: list, process: list) -> Generator:
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
            message_history=str(message_history),
            process=str(process),
        )

        response, _ = self.llm_facade.call(prompt, max_tokens=200, temperature=0.5)

        yield from self._process_streaming_response(response)

    def _process_streaming_response(
        self, response: Stream[ChatCompletionChunk] | MessageStreamManager
    ) -> Generator:
        if self.provider == Provider.OPENAI:
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        elif self.provider == Provider.ANTHROPIC:
            with response as stream:
                for text in stream.text_stream:
                    yield text
        else:
            raise Exception("Invalid provider")
