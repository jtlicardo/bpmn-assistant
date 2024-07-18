from unittest.mock import Mock

import pytest

from bpmn_assistant.core import LLMFacade
from bpmn_assistant.services import BpmnModelingService


class TestCreateBpmn:

    @pytest.mark.skip(reason="Test with real API")
    def test_create_bpmn(self, message_history_create_bpmn, openai_facade):
        bpmn_service = BpmnModelingService()

        result = bpmn_service.create_bpmn(openai_facade, message_history_create_bpmn)

        print(result)

        assert True

    def test_create_bpmn_raises_exception_for_missing_id(self):
        bpmn_service = BpmnModelingService()
        mock_llm_facade = Mock(LLMFacade)

        invalid_process = {
            "process": [
                {"type": "startEvent", "next": "task1"},
                {
                    "id": "task1",
                    "type": "task",
                    "label": "Perform task",
                    "next": "end1",
                },
                {"id": "end1", "type": "endEvent", "next": None},
            ]
        }

        mock_llm_facade.call.return_value = (invalid_process, None)

        with pytest.raises(Exception) as e:
            bpmn_service.create_bpmn(mock_llm_facade, [])

        assert "Max number of retries reached" in str(e.value)
        assert mock_llm_facade.call.call_count == 4

    def test_create_bpmn_raises_exception_if_element_points_to_parent_gateway(self):
        bpmn_service = BpmnModelingService()
        mock_llm_facade = Mock(LLMFacade)

        invalid_process = {
            "process": [
                {"type": "startEvent", "id": "start1", "next": "task1"},
                {
                    "type": "exclusiveGateway",
                    "id": "exclusive1",
                    "label": "Product in stock?",
                    "branches": [
                        {
                            "condition": "Product is out of stock",
                            "path": [
                                {
                                    "type": "task",
                                    "id": "task2",
                                    "label": "Notify customer that order cannot be fulfilled",
                                    "next": "exclusive1",
                                },
                            ],
                        },
                        {
                            "condition": "Product is in stock",
                            "path": [
                                {
                                    "type": "task",
                                    "id": "task3",
                                    "label": "Notify customer that order cannot be fulfilled",
                                    "next": "end1",
                                },
                            ],
                        },
                    ],
                },
                {"type": "endEvent", "id": "end1", "next": None},
            ]
        }

        mock_llm_facade.call.return_value = (invalid_process, None)

        with pytest.raises(Exception) as e:
            bpmn_service.create_bpmn(mock_llm_facade, [])

        assert "Max number of retries reached" in str(e.value)
        assert mock_llm_facade.call.call_count == 4
