from unittest.mock import Mock

import pytest

from bpmn_assistant.core import LLMFacade
from bpmn_assistant.services import BpmnModelingService


class TestCreateBpmn:

    def test_create_bpmn_raises_exception_for_missing_id(self):
        bpmn_service = BpmnModelingService()
        mock_llm_facade = Mock(LLMFacade)

        invalid_process = {
            "process": [
                {"type": "startEvent"},
                {
                    "id": "task1",
                    "type": "task",
                    "label": "Perform task",
                },
                {"id": "end1", "type": "endEvent"},
            ]
        }

        mock_llm_facade.call.return_value = invalid_process

        with pytest.raises(ValueError) as e:
            bpmn_service.create_bpmn(mock_llm_facade, [])

        assert "Max number of retries reached" in str(e.value)
        assert mock_llm_facade.call.call_count == 3
