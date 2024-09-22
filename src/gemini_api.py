import google.generativeai as genai
import typing_extensions as typing
import logging


class Verification(typing.TypedDict):
    question_id: int
    correct_options: list


class GeminiAPI:
    def __init__(self, **kwargs):
        genai.configure(api_key=kwargs.get('api_key'))
        self.model = genai.GenerativeModel(kwargs.get('model', 'gemini-1.5-pro'))
        self.generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            temperature=kwargs.get('temperature', 0.1),
            max_output_tokens=kwargs.get('max_tokens', 1000),
            # stop_sequences=["x"],
            response_mime_type='application/json',
            # response_schema=list[Verification]
        )

    def generate_response(self, messages):
        try:
            response = self.model.generate_content(messages, generation_config=self.generation_config,)
            return response.text
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return None
