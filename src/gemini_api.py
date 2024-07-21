import google.generativeai as genai


class GeminiAPI:
    def __init__(self, kwargs):
        genai.configure(api_key=kwargs.get('api_key'))
        self.model = genai.Model('model', 'models/chat-bison-001')
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 100)

    def generate_response(self, prompt) -> str:
        try:
            response = self.model.generate_text(
                prompt=prompt,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens
            )
            return response.candidates[0].output
        except genai.APIError as e:
            print(f"API Error: {e}")
        except genai.ModelError as e:
            print(f"Model Error: {e}")
        except genai.Error as e:
            print(f"General Error: {e}")
