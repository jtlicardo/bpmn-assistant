import pytest

from bpmn_assistant.core import MessageItem
from bpmn_assistant.core.enums import AnthropicModels
from bpmn_assistant.services import ConversationalService


class TestConversationalService:

    @pytest.mark.skip(reason="Test with real API")
    def test_respond_to_query(self):
        service = ConversationalService(AnthropicModels.HAIKU.value)

        message_history = [
            MessageItem(role="user", content="Hello!"),
        ]

        response_generator = service.respond_to_query(message_history, None)

        print("RESPONSE:")
        for chunk in response_generator:
            print(chunk, end="", flush=True)

        print()

        assert True

    @pytest.mark.skip(reason="Test with real API")
    def test_make_final_comment(self, linear_process_fixture):
        service = ConversationalService(AnthropicModels.HAIKU.value)

        message_history = [
            MessageItem(role="user", content="Can you help me create a BPMN process?"),
            MessageItem(
                role="assistant",
                content="Sure! What are the steps involved in the process?",
            ),
            MessageItem(
                role="user",
                content="Just a simple process with a start event, some tasks, and an end event.",
            ),
        ]

        response_generator = service.make_final_comment(
            message_history, linear_process_fixture
        )

        print("RESPONSE:")
        for chunk in response_generator:
            print(chunk, end="", flush=True)

        print()

        assert True
