import json
import asyncio
import logging
import sys

from prompts import News, Tasks, Picture
from openai_api import OpenaiAPI
from gemini_api import GeminiAPI
from config import Config
from tg_api import TelegramBot
from crud import get_random_words


LANGUAGES = ['english', 'spanish']

# Configure logging to use StreamHandler to direct logs to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_news(main_model, second_model) -> list:
    news = News()
    news_prompt = news.get_prompt()
    news_str = second_model.generate_response(messages=news_prompt[0]['content'] + news_prompt[1]['content'])
    try:
        news_lst = json.loads(news_str)
        logging.info(f"Generated News: {news_lst}")
    except json.decoder.JSONDecodeError as e:
        logging.error(f"Most likely the News are not in json: {e}")
        logging.info(f"The prompt: {news_prompt[0]['content']}. The output: {news_str}")
        asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=news_str))
        raise ValueError("Failed to get news in JSON format")
    return news_lst


def get_quizzes(model, news: list) -> dict:
    questions = {}
    for language in LANGUAGES:
        daily_word = get_random_words(language, 1)[0].word
        tasks = Tasks(news=news, language=language, word=daily_word)
        questions_prompts = tasks.get_prompt()
        questions_str = model.generate_response(messages=questions_prompts)
        try:
            questions[language] = json.loads(questions_str)
            logging.info(f"Generated Quizzes: {questions[language]}")
        except json.decoder.JSONDecodeError as e:
            error_msg = f"Most likely the Quizzes are not in json format: {e}"
            logging.error(error_msg)
            logging.info(f"The prompt: {questions_prompts[1]['content']}. The output: {questions_prompts}")
            asyncio.run(bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'],
                                         message=questions_prompts[1]['content'] + questions_str))
            raise ValueError(error_msg)
    return questions


def verify(gemini_model: GeminiAPI, openai_model: OpenaiAPI, questions: dict) -> dict:
    good_questions = {language: [] for language in LANGUAGES}
    bad_questions = {language: [] for language in LANGUAGES}
    initial_opinion = {language: [] for language in LANGUAGES}
    second_opinion = {language: [] for language in LANGUAGES}
    third_opinion = {language: [] for language in LANGUAGES}

    for language in LANGUAGES:
        for q in questions[language]:
            d = {'question_id': q['question_id'], 'correct_options': []}
            d['correct_options'].append(q['options'][q['correct_option_id']])
            initial_opinion[language].append(d)
        # second and third opinions for verification
        tasks = Tasks(news=news_lst, language=language)
        verification_prompt = tasks.verify(questions[language])
        gemini_verif_str = gemini_model.generate_response(
            messages=verification_prompt[0]['content'] + " " + verification_prompt[1]['content'])
        try:
            second_opinion[language] = json.loads(gemini_verif_str)
            logging.info(f"Generated Verification: {second_opinion[language]}")
        except Exception as e:
            logging.error(f"Most likely Gemini Verification is not in json format: {e}")
            logging.info(f"The prompt: {verification_prompt[1]['content']}")
            logging.info(f"The output: {json.dumps(gemini_verif_str)}")
            second_opinion[language] = initial_opinion[language]

        openai_verif_str = openai_model.generate_response(messages=verification_prompt)
        try:
            third_opinion[language] = json.loads(openai_verif_str)
            logging.info(f"Generated Verification: {third_opinion[language]}")
        except Exception as e:
            logging.error(f"Most likely OpenAi Verification is not in json format: {e}")
            logging.info(f"The prompt: {verification_prompt[1]['content']}")
            logging.info(f"The output: {json.dumps(openai_verif_str)}")
            third_opinion[language] = initial_opinion[language]

        for q, op2, op3 in zip(questions[language], second_opinion[language], third_opinion[language]):
            if len(q['options']) != len(set(q['options'])):
                bad_questions[language].append(q)
                continue
            if len(op2['correct_options']) != 1 or len(op3['correct_options']) != 1:
                bad_questions[language].append(q)
                continue
            if op2['correct_options'][0] != q['options'][q['correct_option_id']]:
                bad_questions[language].append(q)
                continue
            if op3['correct_options'][0] != q['options'][q['correct_option_id']]:
                bad_questions[language].append(q)
                continue
            good_questions[language].append(q)

    logging.info(f"Questions: {json.dumps(questions)}")
    logging.info(f"The second opinion: {json.dumps(second_opinion)}")
    logging.info(f"The third opinion: {json.dumps(third_opinion)}")
    logging.info(f"Bad questions: {json.dumps(bad_questions)}")
    return {'good': good_questions, 'bad': bad_questions}


def generate_image(image_model, topic: dict) -> dict:
    images = {}
    picture = Picture()
    for language in LANGUAGES:
        picture_prompt = picture.get_picture_prompt(text=json.dumps(topic[language][0]))
        image = image_model.generate_image(prompt=picture_prompt)
        images[language] = image
    return images


if __name__ == "__main__":
    openai = OpenaiAPI(api_key=Config.OPENAI_API_KEY, model='gpt-4.5-preview')
    gemini = GeminiAPI(api_key=Config.GEMINI_API_KEY, model='gemini-2.0-flash')
    bot = TelegramBot(token=Config.TG_TOKEN)

    #### NEWS GENERATION
    news_lst = get_news(main_model=openai, second_model=gemini)

    #### QUIZZES GENERATION
    questions = get_quizzes(model=openai, news=news_lst)

    #### VERIFICATION
    verified_questions = verify(gemini_model=gemini, openai_model=openai, questions=questions)

    #### PICTURE GENERATION
    images = generate_image(image_model=openai, topic=verified_questions['good'])  # news_lst[0]["text"])

    #### TG
    asyncio.run(bot.send_image_quizzes(chats=Config.CHANNEL_ID,
                                       questions=verified_questions['good'],
                                       images=images))
