import pytest

from bpmn_assistant.services.process_editing import define_change_request


class TestDefineChangeRequest:

    @pytest.mark.skip(reason="Test with real API")
    def test_define_change_request(
        self, anthropic_facade, define_change_request_messages_1
    ):
        change_request = define_change_request(
            anthropic_facade, define_change_request_messages_1
        )

        print("CHANGE REQUEST: ", change_request)

        assert True
