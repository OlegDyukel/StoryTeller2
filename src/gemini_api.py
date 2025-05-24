import google.generativeai as genai
import typing_extensions as typing
import logging
from src.interfaces import AITextGenerator


class Verification(typing.TypedDict):
    question_id: int
    correct_options: list


class GeminiAPI(AITextGenerator):
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

    def generate_text(self, prompt: dict, **kwargs) -> str:
        # Assuming prompt is a dict like {"messages": [{"role": "user", "content": "..."}]}
        # based on AITextGenerator interface (prompt: dict)
        # and the need for a list of messages by the Gemini client.
        messages_list = prompt.get('messages')
        if messages_list is None:
            logging.error("GeminiAPI.generate_text: 'messages' key not found in prompt dictionary.")
            # Fallback or error:
            return None # Or raise ValueError

        try:
            # Gemini's generate_content can take the list of message dicts directly.
            # It can also take a simple string if messages_list was just that.
            # Ensure it's in the format it expects (e.g., list of ContentDict).
            # For simplicity, if it's a list of {'role': 'user', 'content': '...'},
            # it should work. Gemini also supports 'parts': [{'text': '...'}]
            # If roles are 'user' and 'model', it should map them correctly.
            response = self.model.generate_content(messages_list, generation_config=self.generation_config,)
            return response.text
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return None
