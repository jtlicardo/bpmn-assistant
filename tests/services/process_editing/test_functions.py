import pytest

from bpmn_assistant.services.process_editing import (
    delete_element,
    redirect_flow,
    add_element,
    move_element,
    update_element,
)


class TestProcessEditingFunctions:
    def test_delete_element(self, order_process_fixture):

        # Delete task1
        result = delete_element(order_process_fixture, "task1")
        updated_process = result["process"]

        # Assert that task1 is no longer in the process
        assert any(element["id"] == "task1" for element in updated_process) == False

        # Assert that the next field of start1 is now exclusive1
        start1 = next(
            element for element in updated_process if element["id"] == "start1"
        )
        assert start1["next"] == "exclusive1"

    def test_delete_element_inside_gateway(self, order_process_fixture):

        # Delete task4
        result = delete_element(order_process_fixture, "task4")
        updated_process = result["process"]

        updated_segment = updated_process[2]["branches"][1]["path"][0]["branches"][0][
            "path"
        ]

        task3 = updated_segment[0]

        # Assert that task4 is no longer in the updated segment
        assert any(element["id"] == "task4" for element in updated_segment) == False

        # Assert that the next field of task3 is now end1
        assert task3["next"] == "end1"

    def test_redirect_flow_inside_gateway(self, order_process_fixture):

        # Redirect the flow from task4 to exclusive1
        result = redirect_flow(order_process_fixture, "task4", "exclusive1")
        updated_process = result["process"]

        updated_segment = updated_process[2]["branches"][1]["path"][0]["branches"][0][
            "path"
        ]

        redirected_element = updated_segment[1]

        # Assert that the next field of task4 is now exclusive1
        assert redirected_element["next"] == "exclusive1"

    def test_redirect_flow_inside_gateway_non_last_element_should_raise_exception(
        self, order_process_fixture
    ):
        with pytest.raises(Exception) as e:
            redirect_flow(order_process_fixture, "task3", "exclusive1")

        assert str(e.value) == "Cannot redirect a non-last element in the list"

    def test_redirect_end_event_should_raise_exception(self, order_process_fixture):
        with pytest.raises(Exception) as e:
            redirect_flow(order_process_fixture, "end1", "start1")

        assert str(e.value) == "Cannot redirect an end event"

    def test_add_element(self, order_process_fixture):

        # Add a new task after task3 (which is inside the exclusiveGateway with id exclusive2)
        new_task = {
            "type": "task",
            "id": "task6",
            "label": "Pack order",
        }

        result = add_element(order_process_fixture, new_task, after_id="task3")
        updated_process = result["process"]

        exclusive1 = next(
            element for element in updated_process if element["id"] == "exclusive1"
        )

        updated_segment = exclusive1["branches"][1]["path"][0]["branches"][0]["path"]

        # Assert that the second element of the segment is now task6
        task6 = updated_segment[1]
        assert task6["id"] == "task6"

        # Assert that the next field of task3 is now task6
        task3 = updated_segment[0]
        assert task3["next"] == "task6"

        # Assert that the next field of task6 is now task4
        assert task6["next"] == "task4"

    def test_add_element_raises_exception_if_element_id_already_exists(
        self, order_process_fixture
    ):

        new_task = {
            "type": "task",
            "id": "task1",
            "label": "Pack order",
        }

        with pytest.raises(Exception) as e:
            add_element(order_process_fixture, new_task)

        assert str(e.value) == "Element with id task1 already exists"

    def test_move_element(self, order_process_fixture):

        result = move_element(order_process_fixture, "task4", before_id="task3")
        updated_process = result["process"]

        updated_segment = updated_process[2]["branches"][1]["path"][0]["branches"][0][
            "path"
        ]

        # Assert that the order of the elements in the segment is now task4, task3
        task4 = updated_segment[0]
        task3 = updated_segment[1]

        assert task4["id"] == "task4"
        assert task3["id"] == "task3"

        # Assert that the next field of task4 is now task3
        assert task4["next"] == "task3"

        # Assert that the next field of task3 is now end1
        assert task3["next"] == "end1"

    def test_update_element(self, order_process_fixture):

        new_type = "serviceTask"
        new_label = "Send email to customer"

        new_element = {
            "type": new_type,
            "id": "task4",
            "label": new_label,
        }

        result = update_element(order_process_fixture, new_element)
        updated_process = result["process"]

        updated_segment = updated_process[2]["branches"][1]["path"][0]["branches"][0][
            "path"
        ]

        # Assert that the label of task4 is now "Send email to customer"
        task4 = updated_segment[1]
        assert task4["label"] == new_label

        # Assert that the type of task4 is now "serviceTask"
        assert task4["type"] == new_type

        # Assert that the next field of task4 is still end1
        assert task4["next"] == "end1"

    def test_update_element_raises_exception_if_element_is_gateway(
        self, order_process_fixture
    ):

        new_element = {
            "type": "exclusiveGateway",
            "id": "exclusive1",
            "label": "New label",
        }

        with pytest.raises(Exception) as e:
            update_element(order_process_fixture, new_element)

        assert str(e.value) == "Cannot update a gateway element"
