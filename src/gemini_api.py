from google.cloud import aiplatform
import vertexai
import logging

KEY_FILE_PATH = r"C:\Users\user\Documents\projects\GPT coach\celtic-ego-255816-637d51daf4e6.json"

class GeminiAPI:
    def __init__(self):
        vertexai.init(project="celtic-ego-255816", location="europe-west3", credentials=KEY_FILE_PATH)
        self.model = "gemini-1.5-pro-001"
        self.parameters = {
            "temperature": 0.7,
            "max_output_tokens": 500,
            "top_p": 0.8,
            "top_k": 40
        }

    def generate_response(self, prompt) -> str:
        try:
            response = vertexai.language_models.generate_text(
                model=self.model,
                prompt=prompt,
                parameters=self.parameters
            )
            content = response.candidates[0].output
            logging.info(content)
            return content
        except vertexai.exceptions.ApiException as e:
            logging.error(f"Vertex AI API Error: {e}")
        except Exception as e:  # Catch any other unexpected errors
            logging.error(f"Unexpected Error: {e}")
        return ""  # Return an empty string in case of errors
