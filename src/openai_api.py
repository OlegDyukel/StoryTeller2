from openai import OpenAI
import openai
from io import BytesIO
from PIL import Image
import requests
import logging
from src.interfaces import AITextGenerator, AIImageGenerator

class OpenaiAPI(AITextGenerator, AIImageGenerator):

    def __init__(self, **kwargs):
        self.client = OpenAI(api_key=kwargs.get('api_key'))
        self.model = kwargs.get('model', 'gpt-4o')
        self.temperature = kwargs.get('temperature', 0.3)
        self.max_tokens = kwargs.get('max_tokens', 1200)

    def generate_text(self, prompt: dict, **kwargs) -> str:
        # Assuming prompt is a dict like {"messages": [{"role": "user", "content": "..."}]}
        # based on AITextGenerator interface (prompt: dict)
        # and the need for a list of messages by the OpenAI client.
        messages_list = prompt.get('messages')
        if messages_list is None:
            logging.error("OpenaiAPI.generate_text: 'messages' key not found in prompt dictionary.")
            # Fallback or error: try to use prompt directly if it's a list (older usage)
            # or if it's the expected message structure itself. This is ambiguous.
            # For now, strict check:
            return None # Or raise ValueError

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages_list,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            content = response.choices[0].message.content.strip()
            logging.info(f"Generated answer: {content}")
            return content
        except openai.APIError as e:
            logging.error(f"An error occurred: {e}")
            return None

    def generate_image(self, prompt: str, **kwargs) -> Image.Image:
        # https://github.com/openai/openai-python/blob/main/examples/picture.py
        try:
            # Request image generation from DALL-E using the updated API
            response = openai.images.generate(prompt=prompt, model=kwargs.get('model', "dall-e-3"))
            # Download the image
            response = requests.get(response.data[0].url)
            image = Image.open(BytesIO(response.content))
            return image
        except openai.OpenAIError as e:
            logging.error(f"An error occurred: {e}")
            return None
