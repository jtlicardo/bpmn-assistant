import pytest

from bpmn_assistant.services.process_editing import (
    delete_element,
    redirect_branch,
    add_element,
    move_element,
    update_element,
)


class TestProcessEditingFunctions:
    def test_delete_element(self, order_process):
        result = delete_element(order_process, "task1")
        process = result["process"]
        assert any(element["id"] == "task1" for element in process) is False

    def test_delete_element_2(self, order_process):
        result = delete_element(order_process, "task2")
        process = result["process"]
        updated_segment = process[2]["branches"][0]["path"]
        assert updated_segment == []

    def test_delete_element_3(self, order_process):
        result = delete_element(order_process, "task4")
        process = result["process"]
        updated_segment = process[2]["branches"][1]["path"][0]["branches"][0]["path"]
        assert any(element["id"] == "task4" for element in updated_segment) is False

    def test_redirect_flow(self, order_process):
        result = redirect_branch(order_process, "Payment succeeds", "exclusive1")
        updated_process = result["process"]
        updated_branch = updated_process[2]["branches"][1]["path"][0]["branches"][0]
        assert updated_branch["next"] == "exclusive1"

    def test_add_element(self, order_process):
        new_task = {
            "type": "task",
            "id": "task6",
            "label": "Pack order",
        }

        result = add_element(order_process, new_task, after_id="task3")
        updated_process = result["process"]
        exclusive1 = next(el for el in updated_process if el["id"] == "exclusive1")
        updated_segment = exclusive1["branches"][1]["path"][0]["branches"][0]["path"]
        task6 = updated_segment[1]
        assert task6["id"] == "task6"

    def test_add_element_raises_exception_if_element_id_already_exists(
        self, order_process
    ):
        new_task = {
            "type": "task",
            "id": "task1",
            "label": "Pack order",
        }
        with pytest.raises(Exception) as e:
            add_element(order_process, new_task)
        assert str(e.value) == "Element with id task1 already exists"

    def test_move_element(self, order_process):
        result = move_element(order_process, "task4", before_id="task3")
        updated_process = result["process"]
        updated_segment = updated_process[2]["branches"][1]["path"][0]["branches"][0][
            "path"
        ]
        task4 = updated_segment[0]
        task3 = updated_segment[1]
        assert task4["id"] == "task4"
        assert task3["id"] == "task3"

    def test_update_element(self, order_process):
        new_type = "serviceTask"
        new_label = "Send email to customer"
        new_element = {
            "type": new_type,
            "id": "task4",
            "label": new_label,
        }

        result = update_element(order_process, new_element)
        updated_process = result["process"]
        updated_segment = updated_process[2]["branches"][1]["path"][0]["branches"][0][
            "path"
        ]
        task4 = updated_segment[1]
        assert task4["label"] == new_label
        assert task4["type"] == new_type
