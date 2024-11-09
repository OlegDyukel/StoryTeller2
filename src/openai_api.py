from openai import OpenAI
import openai
from io import BytesIO
from PIL import Image
import requests
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

    def generate_image(self, prompt, model="dall-e-3"):
        # https://github.com/openai/openai-python/blob/main/examples/picture.py
        try:
            # Request image generation from DALL-E using the updated API
            response = openai.images.generate(prompt=prompt, model=model)
            # Download the image
            response = requests.get(response.data[0].url)
            image = Image.open(BytesIO(response.content))
            return image
        except openai.OpenAIError as e:
            logging.error(f"An error occurred: {e}")
            return None
