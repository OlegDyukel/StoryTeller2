import json
import asyncio
import logging

from prompts import News, Tasks
from openai_api import OpenaiAPI
from config import Config
from tg_api import TelegramBot


if __name__ == "__main__":
    language = 'English'
    openai = OpenaiAPI(api_key=Config.OPENAI_API_KEY, model='gpt-4o')

    #### NEWS GENERATION
    news = News()
    news_messages = news.get_prompt()
    news = openai.generate_response(messages=news_messages)
    try:
        news_lst = json.loads(news)
        logging.info(f"Generated News: {news_lst}")
    except json.decoder.JSONDecodeError as e:
        logging.error(f"Most likely the News are not in json: {e}")
        logging.info(f"The output: {news_messages}")
        raise "Failed to get news in JSON format"

    #### QUIZZES GENERATION
    tasks = Tasks(news=news_lst, language=language)
    questions_messages = tasks.get_prompt()
    questions = openai.generate_response(messages=questions_messages)
    try:
        questions_lst = json.loads(questions)
        logging.info(f"Generated News: {questions_lst}")
    except json.decoder.JSONDecodeError as e:
        logging.error(f"Most likely the Quizzes are not in json format: {e}")
        logging.info(f"The output: {questions_messages}")
        raise

    #### VERRIFICATION BY OTHER AI


    ############## TG #########
    bot = TelegramBot(token=Config.TG_TOKEN)
    # asyncio.run(bot.send_message(chat_id=Config.CHANNEL_ID, message=news))
    asyncio.run(bot.send_quizzes(chat_id=Config.CHANNEL_ID, questions_list=questions_lst))
