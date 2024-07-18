import pytest

from bpmn_assistant.services import determine_intent


class TestDetermineIntent:

    @pytest.mark.skip(reason="Test with real API")
    def test_determine_intent(self, message_history_create_bpmn, openai_facade):

        print("\nDETERMINE INTENT")
        result = determine_intent(openai_facade, message_history_create_bpmn)

        print(result)

        assert True
