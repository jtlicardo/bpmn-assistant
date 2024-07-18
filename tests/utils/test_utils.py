from bpmn_assistant.utils import message_history_to_string


class TestUtils:

    def test_message_history_to_string(self, message_history_create_bpmn):

        message_history_string = message_history_to_string(message_history_create_bpmn)

        expected_string = "User: Can you help me create a BPMN process?\nAssistant: Sure! What are the steps involved in the process?\nUser: Create a process that involves a user signing up for a service. 1. The user visits the website and clicks on the 'Sign Up' button. 2. The user enters their email address and password. 3. The user clicks on the 'Sign Up' button. 4. The user receives a confirmation email. 5. The user clicks on the confirmation link in the email. 6. The user is redirected to the website and sees a confirmation message."

        assert message_history_string == expected_string