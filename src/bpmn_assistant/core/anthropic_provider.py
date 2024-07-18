import json

from anthropic import Anthropic

from bpmn_assistant.config import logger
from .enums import AnthropicModels
from .llm_provider import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, output_mode: str, streaming: bool):
        self.api_key = api_key
        self.output_mode = output_mode
        self.streaming = streaming
        self.client = Anthropic(api_key=self.api_key)

    def call(self, model: str, messages: list, max_tokens: int, temperature: float):
        """
        Implementation of the Anthropic API call.
        """
        client = Anthropic(api_key=self.api_key)

        if self.output_mode == "json":
            # We add "{" to constrain the model to output a JSON object
            messages.append({"role": "assistant", "content": "{"})

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are a helpful assistant designed to output JSON.",
                messages=messages,
            )

            # Remove the "{" we added from the messages
            messages.pop()

            raw_output = response.content[0].text

            # Add "{" back to the raw output to make it a valid JSON object
            raw_output = "{" + raw_output

            return self._process_response(raw_output, messages)
        else:
            if self.streaming:
                streaming_response = client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                )
                return streaming_response, messages
            else:
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                )

                raw_output = response.content[0].text

                return self._process_response(raw_output, messages)

    def get_initial_messages(self):
        return []

    def check_model_compatibility(self, model: str) -> bool:
        return model in [m.value for m in AnthropicModels]

    def _process_response(self, raw_output, messages) -> tuple:
        """
        Process the raw output from the model. Returns the appropriate response based on the output mode.
        If the output mode is JSON, the raw output is parsed and returned as a JSON object.
        If the output mode is text, the raw output is returned as is.
        """
        if self.output_mode == "json":
            try:
                json_object = json.loads(raw_output)
                messages.append(
                    {"role": "assistant", "content": json.dumps(json_object)}
                )
                return json_object, messages
            except json.decoder.JSONDecodeError as e:
                logger.error(f"JSONDecodeError, check raw_output.txt. {e}")
                with open("raw_output.txt", "w", encoding="utf-8") as f:
                    f.write(raw_output)
                raise Exception("Invalid JSON response from Anthropic")
        elif self.output_mode == "text":
            messages.append({"role": "assistant", "content": raw_output})
            return raw_output, messages
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")
