import os

import pytest
from dotenv import load_dotenv

from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.core.enums import Provider, AnthropicModels, OpenAIModels
from tests.fixtures.bpmn_loader import load_bpmn


@pytest.fixture
def anthropic_facade():
    load_dotenv(override=True)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return LLMFacade(Provider.ANTHROPIC, api_key, AnthropicModels.HAIKU.value)


@pytest.fixture
def openai_facade():
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    return LLMFacade(Provider.OPENAI, api_key, OpenAIModels.GPT_4O_MINI.value)


@pytest.fixture
def order_process_fixture():
    """
    Description: An ordering process that contains 2 exclusive gateways, one
    of which is nested inside the other.
    """
    return [
        {"type": "startEvent", "id": "start1"},
        {
            "type": "task",
            "id": "task1",
            "label": "Receive order from customer",
        },
        {
            "type": "exclusiveGateway",
            "id": "exclusive1",
            "label": "Product in stock?",
            "has_join": False,
            "branches": [
                {
                    "condition": "Product is out of stock",
                    "path": [
                        {
                            "type": "task",
                            "id": "task2",
                            "label": "Notify customer that order cannot be fulfilled",
                        },
                    ],
                },
                {
                    "condition": "Product is in stock",
                    "path": [
                        {
                            "type": "exclusiveGateway",
                            "id": "exclusive2",
                            "label": "Payment succeeds?",
                            "has_join": False,
                            "branches": [
                                {
                                    "condition": "Payment succeeds",
                                    "path": [
                                        {
                                            "type": "task",
                                            "id": "task3",
                                            "label": "Process order",
                                        },
                                        {
                                            "type": "task",
                                            "id": "task4",
                                            "label": "Notify customer that order has been processed",
                                        },
                                    ],
                                },
                                {
                                    "condition": "Payment fails",
                                    "path": [
                                        {
                                            "type": "task",
                                            "id": "task5",
                                            "label": "Notify customer that order cannot be processed",
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                },
            ],
        },
        {"type": "endEvent", "id": "end1"},
    ]


@pytest.fixture
def procurement_process_fixture():
    """
    Description: A procurement process that involves two parallel branches.
    """
    return [
        {"type": "startEvent", "id": "start1"},
        {
            "type": "parallelGateway",
            "id": "parallel1",
            "branches": [
                [
                    {
                        "type": "task",
                        "id": "task1",
                        "label": "Send mail to supplier",
                    },
                    {
                        "type": "task",
                        "id": "task2",
                        "label": "Prepare the documents",
                    },
                ],
                [
                    {
                        "type": "task",
                        "id": "task3",
                        "label": "Search for the goods",
                    },
                    {
                        "type": "task",
                        "id": "task4",
                        "label": "Pick up the goods",
                    },
                ],
            ],
        },
        {"type": "endEvent", "id": "end1"},
    ]


@pytest.fixture
def linear_process_fixture():
    """
    Description: A linear process that involves a sequence of tasks.
    """
    return [
        {"type": "startEvent", "id": "start1"},
        {
            "type": "task",
            "id": "task1",
            "label": "Receive customer inquiry",
        },
        {
            "type": "userTask",
            "id": "task2",
            "label": "Review product catalog",
        },
        {"type": "task", "id": "task3", "label": "Prepare quote"},
        {
            "type": "serviceTask",
            "id": "task4",
            "label": "Send quote to customer",
        },
        {
            "type": "task",
            "id": "task5",
            "label": "Follow up with customer",
        },
        {"type": "endEvent", "id": "end1"},
    ]


@pytest.fixture
def pg_inside_eg_fixture():
    """
    Description: A process that includes an exclusive gateway, with one of the
    branches containing a parallel gateway.
    """
    return [
        {"type": "startEvent", "id": "start1"},
        {
            "type": "exclusiveGateway",
            "id": "exclusive1",
            "label": "Exclusive Decision",
            "has_join": True,
            "branches": [
                {
                    "condition": "Condition A",
                    "path": [
                        {
                            "type": "task",
                            "id": "task2",
                            "label": "Task A",
                        },
                    ],
                },
                {
                    "condition": "Condition B",
                    "path": [
                        {
                            "type": "parallelGateway",
                            "id": "parallel1",
                            "branches": [
                                [
                                    {
                                        "type": "task",
                                        "id": "task3",
                                        "label": "Parallel Task 1",
                                    },
                                ],
                                [
                                    {
                                        "type": "task",
                                        "id": "task4",
                                        "label": "Parallel Task 2",
                                    },
                                ],
                            ],
                        }
                    ],
                },
            ],
        },
        {"type": "endEvent", "id": "end1"},
    ]


def dict_to_message_item(message_dict):
    return MessageItem(**message_dict)


def convert_message_history(message_history):
    return [dict_to_message_item(message) for message in message_history]


@pytest.fixture
def message_history_create_bpmn():
    """
    Description: A message history that contains a conversation between a user and an assistant.
    The user is asking the assistant to help them create a BPMN process.
    """
    message_history = [
        {"role": "user", "content": "Can you help me create a BPMN process?"},
        {
            "role": "assistant",
            "content": "Sure! What are the steps involved in the process?",
        },
        {
            "role": "user",
            "content": "Create a process that involves a user signing up for a service. 1. The user visits the website and clicks on the 'Sign Up' button. 2. The user enters their email address and password. 3. The user clicks on the 'Sign Up' button. 4. The user receives a confirmation email. 5. The user clicks on the confirmation link in the email. 6. The user is redirected to the website and sees a confirmation message.",
        },
    ]

    return convert_message_history(message_history)


@pytest.fixture
def message_history_combine_tasks():
    """
    Description: A message history that contains a conversation between a user and an assistant.
    The user is asking the assistant to combine two tasks in a BPMN process.
    """
    message_history = [
        {
            "role": "user",
            "content": "Can you help me create a BPMN process for a university exam?",
        },
        {
            "role": "assistant",
            "content": "Sure! What are the steps involved in the process?",
        },
        {
            "role": "user",
            "content": "The process involves logging in to the university's website, taking an online exam, "
            "grading the exam, and entering the grade.",
        },
        {
            "role": "assistant",
            "content": "I created the process! You can see it in the right panel.",
        },
        {
            "role": "user",
            "content": "Can you combine the tasks for logging in to the university website and taking an online exam?",
        },
    ]

    return convert_message_history(message_history)


@pytest.fixture
def message_history_explain_process():
    """
    Description: A message history that contains a conversation between a user and an assistant.
    The user is asking the assistant to explain the BPMN process that was created.
    """
    message_history = [
        {
            "role": "user",
            "content": "Can you help me create a BPMN process for a university exam?",
        },
        {
            "role": "assistant",
            "content": "Sure! What are the steps involved in the process?",
        },
        {
            "role": "user",
            "content": "The process involves logging in to the university's website, taking an online exam, "
            "grading the exam, and entering the grade.",
        },
        {
            "role": "assistant",
            "content": "I created the process! You can see it in the right panel.",
        },
        {
            "role": "user",
            "content": "Can you explain what you did?",
        },
    ]

    return convert_message_history(message_history)


@pytest.fixture
def bpmn_xml_linear_process():
    """
    Description: A BPMN XML string that represents a linear process.
    """
    return load_bpmn("linear_process.bpmn")


@pytest.fixture
def bpmn_xml_exclusive_gateway():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway.
    """
    return load_bpmn("exclusive_gateway.bpmn")


@pytest.fixture
def bpmn_xml_exclusive_gateway_join():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway that has a join gateway.
    """
    return load_bpmn("exclusive_gateway_join.bpmn")


@pytest.fixture
def bpmn_xml_nested_exclusive_gateway():
    """
    Description: A BPMN XML string that represents a process with a nested exclusive gateway.
    """
    return load_bpmn("nested_exclusive_gateway.bpmn")


@pytest.fixture
def bpmn_xml_parallel_gateway():
    """
    Description: A BPMN XML string that represents a process with a parallel gateway.
    """
    return load_bpmn("parallel_gateway.bpmn")


@pytest.fixture
def bpmn_xml_pg_inside_eg():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway that contains a parallel gateway.
    """
    return load_bpmn("pg_inside_eg.bpmn")


@pytest.fixture
def bpmn_xml_eg_inside_pg():
    """
    Description: A BPMN XML string that represents a process with a parallel gateway that contains an exclusive gateway.
    """
    return load_bpmn("eg_inside_pg.bpmn")


@pytest.fixture
def bpmn_xml_eg_next():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway that contains a loop (empty
    path).
    """
    return load_bpmn("eg_next.bpmn")


@pytest.fixture
def bpmn_xml_eg_next_2():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway that contains a loop
    (non-empty path).
    """
    return load_bpmn("eg_next_2.bpmn")


@pytest.fixture
def bpmn_xml_eg_next_3():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway that contains a loop with a
    parallel gateway.
    """
    return load_bpmn("eg_next_3.bpmn")


@pytest.fixture
def bpmn_xml_eg_next_4():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway that contains a loop with
    another exclusive gateway.
    """
    return load_bpmn("eg_next_4.bpmn")


@pytest.fixture
def bpmn_xml_eg_next_5():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway that contains a loop with
    another exclusive gateway (join).
    """
    return load_bpmn("eg_next_5.bpmn")


@pytest.fixture
def bpmn_xml_eg_empty_path():
    """
    Description: A BPMN XML string that represents a process with an exclusive gateway that contains an empty path.
    """
    return load_bpmn("eg_empty_path.bpmn")
