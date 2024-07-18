import os

import pytest
from dotenv import load_dotenv

from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.core.enums import Provider, AnthropicModels, OpenAIModels


@pytest.fixture
def anthropic_facade():
    load_dotenv(override=True)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return LLMFacade(Provider.ANTHROPIC.value, api_key, AnthropicModels.HAIKU.value)


@pytest.fixture
def openai_facade():
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    return LLMFacade(Provider.OPENAI.value, api_key, OpenAIModels.GPT_4O_MINI.value)


@pytest.fixture
def order_process_fixture():
    """
    Description: An ordering process that contains 2 exclusive gateways, one
    of which is nested inside the other.
    """
    return [
        {"type": "startEvent", "id": "start1", "next": "task1"},
        {
            "type": "task",
            "id": "task1",
            "label": "Receive order from customer",
            "next": "exclusive1",
        },
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
                            "next": "end1",
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
                            "branches": [
                                {
                                    "condition": "Payment succeeds",
                                    "path": [
                                        {
                                            "type": "task",
                                            "id": "task3",
                                            "label": "Process order",
                                            "next": "task4",
                                        },
                                        {
                                            "type": "task",
                                            "id": "task4",
                                            "label": "Notify customer that order has been processed",
                                            "next": "end1",
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
                                            "next": "end1",
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                },
            ],
        },
        {"type": "endEvent", "id": "end1", "next": None},
    ]


@pytest.fixture
def procurement_process_fixture():
    """
    Description: A procurement process that involves two parallel branches.
    """
    return [
        {"type": "startEvent", "id": "start1", "next": "parallel1"},
        {
            "type": "parallelGateway",
            "id": "parallel1",
            "branches": [
                [
                    {
                        "type": "task",
                        "id": "task1",
                        "label": "Send mail to supplier",
                        "next": "task2",
                    },
                    {
                        "type": "task",
                        "id": "task2",
                        "label": "Prepare the documents",
                        "next": "join1",
                    },
                ],
                [
                    {
                        "type": "task",
                        "id": "task3",
                        "label": "Search for the goods",
                        "next": "task4",
                    },
                    {
                        "type": "task",
                        "id": "task4",
                        "label": "Pick up the goods",
                        "next": "join1",
                    },
                ],
            ],
        },
        {"type": "parallelGateway", "id": "join1", "next": "end1"},
        {"type": "endEvent", "id": "end1", "next": None},
    ]


@pytest.fixture
def linear_process_fixture():
    """
    Description: A linear process that involves a sequence of tasks.
    """
    return [
        {"type": "startEvent", "id": "start1", "next": "task1"},
        {
            "type": "task",
            "id": "task1",
            "label": "Receive customer inquiry",
            "next": "task2",
        },
        {
            "type": "userTask",
            "id": "task2",
            "label": "Review product catalog",
            "next": "task3",
        },
        {"type": "task", "id": "task3", "label": "Prepare quote", "next": "task4"},
        {
            "type": "serviceTask",
            "id": "task4",
            "label": "Send quote to customer",
            "next": "task5",
        },
        {
            "type": "task",
            "id": "task5",
            "label": "Follow up with customer",
            "next": "end1",
        },
        {"type": "endEvent", "id": "end1", "next": None},
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
