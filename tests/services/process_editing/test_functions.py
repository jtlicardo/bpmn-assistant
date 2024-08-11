import pytest

from bpmn_assistant.services.process_editing import (
    delete_element,
    redirect_branch,
    add_element,
    move_element,
    update_element,
)


class TestProcessEditingFunctions:
    def test_delete_element(self, order_process_fixture):
        result = delete_element(order_process_fixture, "task1")
        process = result["process"]
        assert any(element["id"] == "task1" for element in process) is False

    def test_delete_element_2(self, order_process_fixture):
        result = delete_element(order_process_fixture, "task2")
        process = result["process"]
        updated_segment = process[2]["branches"][0]["path"]
        assert updated_segment == []

    def test_delete_element_3(self, order_process_fixture):
        result = delete_element(order_process_fixture, "task4")
        process = result["process"]
        updated_segment = process[2]["branches"][1]["path"][0]["branches"][0]["path"]
        assert any(element["id"] == "task4" for element in updated_segment) is False

    def test_redirect_flow(self, order_process_fixture):
        result = redirect_branch(
            order_process_fixture, "Payment succeeds", "exclusive1"
        )
        updated_process = result["process"]
        updated_branch = updated_process[2]["branches"][1]["path"][0]["branches"][0]
        assert updated_branch["next"] == "exclusive1"

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
