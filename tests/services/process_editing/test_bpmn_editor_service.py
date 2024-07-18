from unittest.mock import Mock

import pytest

from bpmn_assistant.core import LLMFacade
from bpmn_assistant.services.process_editing import BpmnEditorService


class TestEditBpmn:
    # TODO: fix this test
    @pytest.mark.skip(reason="Not implemented")
    def test_edit_bpmn(self, order_process_fixture):
        mock_llm_facade = Mock(LLMFacade)

        # Define the return values for each call
        mock_llm_facade.call.side_effect = [
            (
                {
                    "function": "delete_element",
                    "arguments": {"element_id": "exclusive1"},
                },
                None,
            ),
            ({"stop": True}, None),
        ]

        change_request = (
            "Redirect 'Notify customer' task to 'Receive order from customer' task."
        )

        bpmn_editor_service = BpmnEditorService(
            mock_llm_facade, order_process_fixture, change_request
        )

        updated_process = bpmn_editor_service.edit_bpmn()

        print("FINAL UPDATED PROCESS: ", updated_process)

        assert True
