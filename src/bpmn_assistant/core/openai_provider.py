import json

from openai import OpenAI

from bpmn_assistant.config import logger
from .enums import OpenAIModels, OutputMode
from .llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(
        self, api_key: str, output_mode: OutputMode = OutputMode.JSON, streaming: bool = False
    ):
        self.api_key = api_key
        self.output_mode = output_mode
        self.streaming = streaming
        self.client = OpenAI(api_key=self.api_key)

    def call(self, model: str, messages: list, max_tokens: int, temperature: float):
        """
        Implementation of the OpenAI API call.
        """
        client = OpenAI(api_key=self.api_key)

        if self.output_mode == OutputMode.JSON:
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            raw_output = response.choices[0].message.content

            return self._process_response(raw_output, messages)
        else:
            if self.streaming:
                streaming_response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                )
                return streaming_response, messages
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                raw_output = response.choices[0].message.content

                return self._process_response(raw_output, messages)

    def get_initial_messages(self):
        return (
            [
                {
                    "role": "system",
                    "content": "You are a helpful assistant designed to output JSON.",
                }
            ]
            if self.output_mode == OutputMode.JSON
            else []
        )

    def check_model_compatibility(self, model: str) -> bool:
        return model in [m.value for m in OpenAIModels]

    def _process_response(self, raw_output, messages) -> tuple:
        """
        Process the raw output from the model. Returns the appropriate response based on the output mode.
        If the output mode is JSON, the raw output is parsed and returned as a JSON object.
        If the output mode is text, the raw output is returned as is.
        """
        if self.output_mode == OutputMode.JSON:
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
                raise Exception("Invalid JSON response from OpenAI")
        elif self.output_mode == OutputMode.TEXT:
            messages.append({"role": "assistant", "content": raw_output})
            return raw_output, messages
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")
