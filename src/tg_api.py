import telegram
import time
import random
import logging

class TelegramBot:
    def __init__(self, token):
        self.bot = telegram.Bot(token=token)

    async def send_message(self, chat_id, message):
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            logging.info(f"Message {message} sent successfully")
        except Exception as e:
            logging.error(f"Error sending message: {e}. Tried to send: {message}")

    async def send_quizzes(self, chats: dict, questions: dict):
        for language, questions_lst in questions.items():
            for question in questions_lst:
                try:
                    await self.bot.send_poll(
                        chat_id=chats[language],
                        question="Topic: " + question['grammar_topic'] + ".\n" + "\n" + question['question'],
                        options=question['options'],
                        type='quiz',
                        correct_option_id=question['correct_option_id'],
                        explanation=question['explanation'],
                        is_anonymous=True
                    )
                    logging.info(f"Quiz sent successfully: {question}")
                except Exception as e:
                    logging.error(f"An error occurred: {e}. Tried to send {question}")
                sleep_time = random.randint(5, 9)
                time.sleep(sleep_time)
