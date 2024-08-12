import telegram
import time
import random

class TelegramBot:
    def __init__(self, token):
        self.bot = telegram.Bot(token=token)

    async def send_message(self, chat_id, message):
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            print("Message sent successfully")
        except Exception as e:
            print(f"Error sending message: {e}")

    async def send_quizzes(self, chat_id: str, questions_list: list):
        for question in questions_list:
            try:
                await self.bot.send_poll(
                    chat_id=chat_id,
                    question="Topic: " + question['grammar_topic'] + ".\n" + question['question'],
                    options=question['options'],
                    type='quiz',
                    correct_option_id=question['correct_option_id'],
                    explanation=question['explanation'],
                    is_anonymous=True
                )
                print("Quiz sent successfully")
                sleep_time = random.randint(5, 9)
                time.sleep(sleep_time)
            except Exception as e:
                print(f"An error occurred: {e}")
