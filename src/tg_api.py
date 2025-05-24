import telegram
import time
import random
import logging
from io import BytesIO
from PIL import Image
from src.interfaces import MessagingService

class TelegramBot(MessagingService):
    def __init__(self, token):
        self.bot = telegram.Bot(token=token)

    async def send_message(self, chat_id: str, message: str, **kwargs) -> None:
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            logging.info(f"Message {message} sent successfully")
        except Exception as e:
            logging.error(f"Error sending message: {e}. Tried to send: {message}")

    async def send_poll(self, chat_id: str, question: str, options: list, correct_option_id: int, explanation: str, **kwargs) -> None:
        try:
            await self.bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=options,
                type='quiz',
                correct_option_id=correct_option_id,
                explanation=explanation,
                is_anonymous=True
            )
            logging.info(f"Poll sent successfully: {question}")
        except Exception as e:
            logging.error(f"An error occurred: {e}. Tried to send {question}")
        # TODO: The original send_quizzes had a sleep, consider if it's needed here or in the calling code.
        # sleep_time = random.randint(5, 9)
        # time.sleep(sleep_time)

    async def send_image(self, chat_id: str, image: Image.Image, caption: str = None, **kwargs) -> None:
        try:
            # Convert the PIL image to a byte array
            byte_array = BytesIO()
            image.save(byte_array, format='PNG')
            byte_array.seek(0)

            # Send the image to the specified chat
            await self.bot.send_photo(chat_id=chat_id, photo=byte_array, caption=caption)
            logging.info(f"Image successfully posted to Telegram channel {chat_id}.")
        except Exception as e:
            logging.error(f"Error occurred while posting image to Telegram: {e}")

    # The following methods are kept for now but should be refactored or removed
    # if their functionality is fully covered by the interface methods.
    async def send_quizzes(self, chats: dict, questions: dict):
        for language, questions_lst in questions.items():
            chat_id_for_poll = chats.get(language) # Get chat_id for the language
            if not chat_id_for_poll:
                logging.warning(f"No chat_id found for language {language} in send_quizzes. Skipping.")
                continue
            for question_data in questions_lst:
                # Construct the full question string similar to the original logic
                full_question_str = "Topic: " + question_data['grammar_topic'] + ".\n" + "\n" + question_data['question']
                await self.send_poll(
                    chat_id=chat_id_for_poll,
                    question=full_question_str,
                    options=question_data['options'],
                    correct_option_id=question_data['correct_option_id'],
                    explanation=question_data['explanation']
                )
                # Consider moving sleep to the calling function if needed for rate limiting across different polls
                # sleep_time = random.randint(5, 9) # Removed
                # time.sleep(sleep_time) # Removed

    async def send_bad_quizzes(self, chats: dict, questions: dict):
        # This method seems to send to a specific 'log' chat.
        # It can be adapted or potentially replaced by direct calls to send_poll with the log chat_id.
        log_chat_id = chats.get('log')
        if not log_chat_id:
            logging.error("No 'log' chat_id found in send_bad_quizzes. Cannot send.")
            return
        for language, questions_lst in questions.items(): # Iterates through languages but sends to same log_chat_id
            for question_data in questions_lst:
                full_question_str = "Topic: " + question_data['grammar_topic'] + ".\n" + "\n" + question_data['question']
                await self.send_poll(
                    chat_id=log_chat_id,
                    question=full_question_str,
                    options=question_data['options'],
                    correct_option_id=question_data['correct_option_id'],
                    explanation=question_data['explanation']
                )
                # sleep_time = random.randint(5, 9) # Removed
                # time.sleep(sleep_time) # Removed

    async def send_image_quizzes(self, chats: dict, questions: dict, images: dict):
        for language, questions_lst in questions.items():
            chat_id_for_image_quiz = chats.get(language)
            if not chat_id_for_image_quiz:
                logging.warning(f"No chat_id found for language {language} in send_image_quizzes. Skipping.")
                continue

            image_to_send = images.get(language)
            if image_to_send:
                await self.send_image(chat_id=chat_id_for_image_quiz, image=image_to_send)
            else:
                logging.warning(f"No image found for language {language} in send_image_quizzes.")

            for question_data in questions_lst:
                full_question_str = "Topic: " + question_data['grammar_topic'] + ".\n" + "\n" + question_data['question']
                await self.send_poll(
                    chat_id=chat_id_for_image_quiz,
                    question=full_question_str,
                    options=question_data['options'],
                    correct_option_id=question_data['correct_option_id'],
                    explanation=question_data['explanation']
                )
                # sleep_time = random.randint(5, 9) # Removed
                # time.sleep(sleep_time) # Removed
