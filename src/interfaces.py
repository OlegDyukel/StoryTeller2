from abc import ABC, abstractmethod
from PIL import Image

class AITextGenerator(ABC):
    @abstractmethod
    def generate_text(self, prompt: dict, **kwargs) -> str:
        pass

class AIImageGenerator(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, **kwargs) -> Image.Image:
        pass

class MessagingService(ABC):
    @abstractmethod
    def send_message(self, chat_id: str, message: str, **kwargs) -> None:
        pass

    @abstractmethod
    def send_poll(self, chat_id: str, question: str, options: list, correct_option_id: int, explanation: str, **kwargs) -> None:
        pass

    @abstractmethod
    def send_image(self, chat_id: str, image: Image.Image, caption: str = None, **kwargs) -> None:
        pass
