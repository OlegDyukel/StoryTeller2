import json
import asyncio
import logging

from prompts import News, Tasks
from openai_api import OpenaiAPI
from gemini_api import GeminiAPI
from config import Config
from tg_api import TelegramBot


if __name__ == "__main__":
    languages = ['english', 'spanish']
    openai = OpenaiAPI(api_key=Config.OPENAI_API_KEY, model='gpt-4o')
    gemini = GeminiAPI(api_key=Config.GEMINI_API_KEY, model='gemini-1.5-pro')
    bot = TelegramBot(token=Config.TG_TOKEN)
    #### NEWS GENERATION
    news = News()
    news_messages = news.get_prompt()
    news_str = openai.generate_response(messages=news_messages)
    try:
        news_lst = json.loads(news_str)
        logging.info(f"Generated News: {news_lst}")
    except json.decoder.JSONDecodeError as e:
        logging.error(f"Most likely the News are not in json: {e}")
        logging.info(f"The output: {news_str}")
        asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=news_str))
        raise "Failed to get news in JSON format"

    #### QUIZZES GENERATION
    questions = {}
    verified_questions = {}
    bad_questions = {}
    for language in languages:
        questions[language] = []
        verified_questions[language] = []
        bad_questions[language] = []
        tasks = Tasks(news=news_lst, language=language)
        questions_prompts = tasks.get_prompt()
        questions_str = openai.generate_response(messages=questions_prompts)
        try:
            questions[language] = json.loads(questions_str)
            logging.info(f"Generated News: {questions[language]}")
        except json.decoder.JSONDecodeError as e:
            error_msg = f"Most likely the Quizzes are not in json format: {e}"
            logging.error(error_msg)
            logging.info(f"The output: {questions_prompts}")
            asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=questions_str))
            raise error_msg

        #### VERRIFICATION BY GEMINI
        verification_prompt = tasks.verify(questions[language])
        verified_answers_str = gemini.generate_response(messages=verification_prompt)
        try:
            verified_answers = json.loads(verified_answers_str)
            logging.info(f"Generated News: {verified_answers}")
        except json.decoder.JSONDecodeError as e:
            error_msg = f"Most likely the Quizzes are not in json format: {e}"
            logging.error(error_msg)
            logging.info(f"The output: {verified_answers_str}")
            asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=verified_answers_str))
            raise error_msg
        for va, q in zip(verified_answers, questions[language]):
            if len(va['correct_options']) == 1 and va['correct_options'][0] == q['correct_option_id']:
                verified_questions[language].append(q)
            else:
                bad_questions[language].append(q)

    ############## TG #########
    asyncio.run(bot.send_quizzes(chats=Config.CHANNEL_ID, questions=verified_questions))
    asyncio.run(bot.send_quizzes(chats=Config.LOG_CHANNEL_ID, questions=bad_questions))
    # asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=news_str))
