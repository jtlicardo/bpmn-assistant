import pytest


@pytest.fixture
def define_change_request_messages_1():
    return [
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


@pytest.fixture
def define_change_request_messages_2():
    return [
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
            "content": "After entering the grade, the professor should be notified.",
        },
    ]
