import json
import asyncio
import logging

from prompts import News, Tasks
from openai_api import OpenaiAPI
from gemini_api import GeminiAPI
from config import Config
from tg_api import TelegramBot


LANGUAGES = ['english', 'spanish']

def get_news(main_model, second_model) -> list:
    news = News()
    news_messages = news.get_prompt()
    # news_str = main_model.generate_response(messages=news_messages)
    news_str = second_model.generate_response(messages=news_messages[0]['content'] + news_messages[1]['content'])
    try:
        news_lst = json.loads(news_str)
        logging.info(f"Generated News: {news_lst}")
    except json.decoder.JSONDecodeError as e:
        logging.error(f"Most likely the News are not in json: {e}")
        logging.info(f"The output: {news_str}")
        asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=news_str))
        raise "Failed to get news in JSON format"
    return news_lst


def get_quizzes(model, news: list) -> dict:
    questions = {}
    for language in LANGUAGES:
        questions[language] = []
        tasks = Tasks(news=news, language=language)
        questions_prompts = tasks.get_prompt()
        questions_str = model.generate_response(messages=questions_prompts)
        try:
            questions[language] = json.loads(questions_str)
            logging.info(f"Generated News: {questions[language]}")
        except json.decoder.JSONDecodeError as e:
            error_msg = f"Most likely the Quizzes are not in json format: {e}"
            logging.error(error_msg)
            logging.info(f"The output: {questions_prompts}")
            asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=questions_str))
            raise error_msg
    return questions


def verify(model, questions: dict) -> dict:
    good_questions = {}
    bad_questions = {}
    second_opinion = {}
    for language in LANGUAGES:
        good_questions[language] = []
        second_opinion[language] = []
        bad_questions[language] = []
        tasks = Tasks(news=news_lst, language=language)
        verification_prompt = tasks.verify(questions[language])
        verified_answers_str = model.generate_response(messages=verification_prompt)
        try:
            second_opinion[language] = json.loads(verified_answers_str)
            logging.info(f"Generated News: {second_opinion}")
        except json.decoder.JSONDecodeError as e:
            error_msg = f"Most likely the Quizzes are not in json format: {e}"
            logging.error(error_msg)
            logging.info(f"The output: {verified_answers_str}")
            asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=verified_answers_str))
            raise error_msg

        for va, q in zip(second_opinion[language], questions[language]):
            if len(va['correct_options']) == 1 and va['correct_options'][0] == q['correct_option_id']:
                good_questions[language].append(q)
            else:
                bad_questions[language].append(q)
    return {'verified': good_questions, 'unverified': bad_questions}


if __name__ == "__main__":
    openai = OpenaiAPI(api_key=Config.OPENAI_API_KEY, model='gpt-4o')
    gemini = GeminiAPI(api_key=Config.GEMINI_API_KEY, model='gemini-1.5-flash')
    bot = TelegramBot(token=Config.TG_TOKEN)

    #### NEWS GENERATION
    news_lst = get_news(main_model=openai, second_model=gemini)

    #### QUIZZES GENERATION
    questions = get_quizzes(model=openai, news=news_lst)

    #### VERIFICATION
    verified_questions = verify(model=gemini, questions=questions)

    #### TG
    asyncio.run(bot.send_quizzes(chats=Config.CHANNEL_ID, questions=verified_questions['verified']))
    asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=str(verified_questions['unverified'])))
