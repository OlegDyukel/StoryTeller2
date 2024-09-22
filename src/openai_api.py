from openai import OpenAI
import openai
import logging

class OpenaiAPI:

    def __init__(self, **kwargs):
        self.client = OpenAI(api_key=kwargs.get('api_key'))
        self.model = kwargs.get('model', 'gpt-4o')
        self.temperature = kwargs.get('temperature', 0.3)
        self.max_tokens = kwargs.get('max_tokens', 1200)

    def generate_response(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            content = response.choices[0].message.content.strip()
            logging.info(f"Generated answer: {content}")
            return content
        except openai.APIError as e:
            logging.error(f"An error occurred: {e}")
            return None
