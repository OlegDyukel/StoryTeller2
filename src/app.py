import asyncio
import logging
import sys
import json # Keep for logging if necessary, but primary JSON logic is in generators

# Configuration
from src.config import Config

# AI Model Implementations
from src.openai_api import OpenaiAPI
from src.gemini_api import GeminiAPI

# Messaging Service Implementation
from src.tg_api import TelegramBot

# Generator Classes
from src.generators import (
    NewsGenerator,
    QuizGenerator,
    QuizVerifier,
    ImageGenerator,
    LANGUAGES # Import LANGUAGES constant from generators.py
)

# CRUD operations (still needed for get_random_words, which is used by QuizGenerator internally)
# No, QuizGenerator calls get_random_words internally, so app.py doesn't need it directly.
# from src.crud import get_random_words 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to stdout
        # Optionally, add a FileHandler if you want to log to a file as well
        # logging.FileHandler("app.log") 
    ]
)

if __name__ == "__main__":
    logging.info("Application started.")

    # --- 1. Instantiate Services (AI Models, Messaging) ---
    try:
        openai_service = OpenaiAPI(api_key=Config.OPENAI_API_KEY, model=Config.OPENAI_MODEL) # Using model from Config
        gemini_service = GeminiAPI(api_key=Config.GEMINI_API_KEY, model=Config.GEMINI_MODEL) # Using model from Config
        telegram_bot = TelegramBot(token=Config.TG_TOKEN)
        logging.info("AI services and Telegram bot instantiated.")
    except Exception as e:
        logging.error(f"Failed to instantiate core services: {e}", exc_info=True)
        sys.exit("Core service instantiation failed. Exiting.")

    # --- 2. Instantiate Generator Classes ---
    # Injecting AI model instances and the bot (for error notification)
    # Using Gemini for news (as per original logic: second_model for news)
    news_generator = NewsGenerator(text_generator=gemini_service, error_notifier=telegram_bot)
    # Using OpenAI for quiz generation (as per original logic: main_model for quizzes)
    quiz_generator = QuizGenerator(text_generator=openai_service, error_notifier=telegram_bot, languages=LANGUAGES)
    # Verifier uses both models
    quiz_verifier = QuizVerifier(primary_text_generator=openai_service, verifier_text_generator=gemini_service, languages=LANGUAGES)
    # Image generator uses OpenAI (as per original logic)
    image_generator = ImageGenerator(image_generator_model=openai_service, languages=LANGUAGES)
    logging.info("Generator classes instantiated.")

    # --- 3. Orchestrate Content Generation and Verification ---
    news_articles = []
    all_quizzes = {}
    verified_quizzes_dict = {'good': {lang: [] for lang in LANGUAGES}, 'bad': {lang: [] for lang in LANGUAGES}}
    images_by_lang = {}

    try:
        # --- News Generation ---
        logging.info("Starting news generation...")
        news_articles = news_generator.get_news()
        if not news_articles:
            logging.error("News generation failed or returned empty. Check logs from NewsGenerator.")
            # Depending on desired behavior, could exit or try to proceed without news
            # For now, we'll let it proceed, subsequent steps might fail or do nothing.
        else:
            logging.info(f"Successfully generated {len(news_articles)} news articles.")

        # --- Quiz Generation ---
        if news_articles: # Only generate quizzes if news was successfully fetched
            logging.info("Starting quiz generation...")
            all_quizzes = quiz_generator.generate_quizzes(news=news_articles)
            if not any(all_quizzes.values()): # Check if any quizzes were generated for any language
                logging.warning("Quiz generation resulted in no quizzes for any language.")
            else:
                for lang, q_list in all_quizzes.items():
                    logging.info(f"Generated {len(q_list)} quizzes for {lang}.")
        else:
            logging.warning("Skipping quiz generation because news generation failed.")

        # --- Quiz Verification ---
        # Proceed with verification even if some languages have no quizzes,
        # QuizVerifier should handle empty lists gracefully.
        if news_articles: # Verification context might depend on news articles
            logging.info("Starting quiz verification...")
            verified_quizzes_dict = quiz_verifier.verify_quizzes(questions_by_lang=all_quizzes, news_articles=news_articles)
            good_quizzes = verified_quizzes_dict.get('good', {})
            bad_quizzes = verified_quizzes_dict.get('bad', {})
            for lang in LANGUAGES:
                logging.info(f"For {lang}: Good quizzes: {len(good_quizzes.get(lang, []))}, Bad quizzes: {len(bad_quizzes.get(lang, []))}")
        else:
            logging.warning("Skipping quiz verification because news generation failed.")
            # Ensure good_quizzes and bad_quizzes are initialized to avoid errors later
            good_quizzes = {lang: [] for lang in LANGUAGES}
            bad_quizzes = {lang: [] for lang in LANGUAGES}


        # --- Image Generation (based on good quizzes) ---
        # Check if there are any good quizzes to generate images for
        if any(good_quizzes.values()):
            logging.info("Starting image generation for good quizzes...")
            images_by_lang = image_generator.generate_images_for_topics(topics_by_lang=good_quizzes)
            for lang, img in images_by_lang.items():
                logging.info(f"Generated image for {lang}: {type(img)}")
        else:
            logging.warning("No good quizzes available to generate images for.")
            
    except ValueError as ve: # Catch ValueErrors raised by generators on critical failures
        logging.error(f"A critical error occurred during content generation: {ve}", exc_info=True)
        # Optionally notify via Telegram about the critical failure
        asyncio.run(telegram_bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=f"Application critical error: {ve}"))
        sys.exit("Content generation pipeline failed. Exiting.")
    except Exception as e:
        logging.error(f"An unexpected error occurred in the generation pipeline: {e}", exc_info=True)
        asyncio.run(telegram_bot.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=f"Application unexpected error: {e}"))
        sys.exit("Unexpected error in pipeline. Exiting.")


    # --- 4. Send Content to Telegram ---
    # Send good quizzes with images
    # The send_image_quizzes method in TelegramBot is expected to handle the logic
    # of sending an image followed by its related quiz polls for each language.
    if any(good_quizzes.values()): # Check if there are any good quizzes to send
        logging.info("Sending good quizzes with images to Telegram channels...")
        try:
            asyncio.run(telegram_bot.send_image_quizzes(
                chats=Config.CHANNEL_ID, # CHANNELS_ID in original config, should be CHANNEL_ID
                questions=good_quizzes,
                images=images_by_lang
            ))
            logging.info("Finished sending good quizzes and images.")
        except Exception as e:
            logging.error(f"Error sending good quizzes with images to Telegram: {e}", exc_info=True)
    else:
        logging.info("No good quizzes were available to send to Telegram.")

    # Send bad quizzes to the log channel for review
    if any(bad_quizzes.values()): # Check if there are any bad quizzes
        logging.info("Sending bad quizzes to log channel...")
        try:
            # send_bad_quizzes expects questions to be a dict like {'language': [quiz_list]}
            # It internally iterates and sends all to the single log channel.
            asyncio.run(telegram_bot.send_bad_quizzes(
                chats={"log": Config.LOG_CHANNEL_ID['log']}, # send_bad_quizzes expects chats['log']
                questions=bad_quizzes
            ))
            logging.info("Finished sending bad quizzes to log channel.")
        except Exception as e:
            logging.error(f"Error sending bad quizzes to Telegram log channel: {e}", exc_info=True)
    else:
        logging.info("No bad quizzes to send to the log channel.")

    logging.info("Application finished.")
