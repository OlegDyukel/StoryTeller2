import json
from openai_api import OpenaiAPI
from config import Config
from tg_api import TelegramBot
import asyncio
from prompts import News, Tasks


if __name__ == "__main__":
    openai = OpenaiAPI(
        api_key=Config.OPENAI_API_KEY,
        model='gpt-4o'
    )
    news = News()
    news_messages = news.get_prompt()
    news = openai.generate_response(messages=news_messages)
    news_lst = json.loads(news)
    if news_lst:
        print(f"Generated News: {news_lst}")
    else:
        print("Failed to generate text.")

    tasks = Tasks(news_lst)
    questions_messages = tasks.get_prompt()
    questions = openai.generate_response(messages=questions_messages)
    questions_lst = json.loads(questions)
    if questions_lst:
        print(f"Generated News: {questions_lst}")
    else:
        print("Failed to generate text.")

    ############## TG #########
    bot = TelegramBot(token=Config.TG_TOKEN)
    # asyncio.run(bot.send_message(chat_id=Config.CHANNEL_ID, message=news))
    asyncio.run(bot.send_quizzes(chat_id=Config.CHANNEL_ID, questions_list=questions_lst))
