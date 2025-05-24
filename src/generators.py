import json
import logging
import asyncio

from src.interfaces import AITextGenerator, MessagingService, AIImageGenerator # Added AIImageGenerator
from src.prompts import News, Tasks, Picture # Added Picture
from src.config import Config
from src.crud import get_random_words
from PIL import Image # Added Image for type hinting, though AIImageGenerator interface uses it.

# Module-level constant for languages
LANGUAGES = ['english', 'spanish']


class NewsGenerator:
    def __init__(self, text_generator: AITextGenerator, error_notifier: MessagingService = None):
        self.text_generator = text_generator
        self.error_notifier = error_notifier

    def get_news(self) -> list:
        news_prompt_generator = News()
        raw_prompt_list = news_prompt_generator.get_prompt() 

        prompt_content_str = ""
        if isinstance(raw_prompt_list, list) and len(raw_prompt_list) >= 1:
            if 'content' in raw_prompt_list[0]:
                prompt_content_str += raw_prompt_list[0]['content']
            if len(raw_prompt_list) >= 2 and 'content' in raw_prompt_list[1]:
                prompt_content_str += " " + raw_prompt_list[1]['content'] 
            elif not prompt_content_str: 
                logging.error("Could not construct meaningful prompt content from News().get_prompt()")
                raise ValueError("Invalid prompt structure from News().get_prompt() for content concatenation.")
        else:
            logging.error(f"News().get_prompt() did not return the expected list of message dictionaries. Received: {raw_prompt_list}")
            raise ValueError("Invalid prompt structure from News().get_prompt()")

        actual_messages_list = [{"role": "user", "content": prompt_content_str.strip()}]
        prompt_for_api = {"messages": actual_messages_list}
        news_str = self.text_generator.generate_text(prompt=prompt_for_api)

        if news_str is None:
            logging.error("Failed to generate news text, text_generator returned None.")
            if self.error_notifier and Config.LOG_CHANNEL_ID and 'log' in Config.LOG_CHANNEL_ID:
                try:
                    asyncio.run(self.error_notifier.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message="NewsGenerator: AI text_generator returned None for news generation."))
                except Exception as e_notify:
                    logging.error(f"Error sending notification via error_notifier: {e_notify}")
            raise ValueError("Failed to generate news text: AI returned None")

        try:
            news_lst = json.loads(news_str)
            logging.info(f"Generated News: {news_lst}")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from news string: {e}")
            logging.info(f"The prompt content was: {prompt_content_str}. The raw output from AI was: {news_str}")
            if self.error_notifier and Config.LOG_CHANNEL_ID and 'log' in Config.LOG_CHANNEL_ID:
                try:
                    asyncio.run(self.error_notifier.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=f"News JSON Decode Error. Raw AI Output: {news_str[:1000]}...")) 
                except Exception as e_notify:
                    logging.error(f"Error sending notification via error_notifier: {e_notify}")
            raise ValueError("Failed to get news in JSON format from AI")
        
        if not isinstance(news_lst, list):
            logging.error(f"Generated news is not a list: {news_lst}")
            if self.error_notifier and Config.LOG_CHANNEL_ID and 'log' in Config.LOG_CHANNEL_ID:
                try:
                    asyncio.run(self.error_notifier.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=f"NewsGenerator: Generated news is not a list. Output: {news_str[:1000]}..."))
                except Exception as e_notify:
                    logging.error(f"Error sending notification via error_notifier: {e_notify}")
            raise ValueError("Generated news is not a list")
            
        return news_lst


class QuizGenerator:
    def __init__(self, text_generator: AITextGenerator, error_notifier: MessagingService = None, languages: list = None):
        self.text_generator = text_generator
        self.error_notifier = error_notifier
        self.languages = languages if languages is not None else LANGUAGES 

    def generate_quizzes(self, news: list) -> dict:
        quizzes_by_language = {}
        for lang in self.languages:
            try:
                random_words_list = get_random_words(lang, 1)
                if not random_words_list:
                    logging.error(f"Could not get random word for language: {lang}")
                    quizzes_by_language[lang] = []
                    continue 
                daily_word = random_words_list[0].word

                tasks_prompt_generator = Tasks(news=news, language=lang, word=daily_word)
                prompt_messages_list = tasks_prompt_generator.get_prompt() 
                prompt_for_api = {"messages": prompt_messages_list}
                quiz_str = self.text_generator.generate_text(prompt=prompt_for_api)

                if quiz_str is None:
                    logging.error(f"Failed to generate quizzes for {lang}, text_generator returned None.")
                    quizzes_by_language[lang] = [] 
                    if self.error_notifier and Config.LOG_CHANNEL_ID and 'log' in Config.LOG_CHANNEL_ID:
                        asyncio.run(self.error_notifier.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=f"QuizGenerator: AI text_generator returned None for {lang}."))
                    continue 

                try:
                    generated_quizzes = json.loads(quiz_str)
                    if not isinstance(generated_quizzes, list):
                        logging.error(f"Generated quizzes for {lang} is not a list: {generated_quizzes}")
                        quizzes_by_language[lang] = []
                        if self.error_notifier and Config.LOG_CHANNEL_ID and 'log' in Config.LOG_CHANNEL_ID:
                             asyncio.run(self.error_notifier.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=f"QuizGenerator: Generated quiz for {lang} is not a list. Output: {quiz_str[:1000]}..."))
                        continue 
                        
                    quizzes_by_language[lang] = generated_quizzes
                    logging.info(f"Generated Quizzes for {lang}: {len(generated_quizzes)} items.")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to decode JSON for {lang} quizzes: {e}")
                    prompt_content_to_log = ""
                    if prompt_messages_list and isinstance(prompt_messages_list, list):
                        for msg in prompt_messages_list: 
                            if msg.get('role') == 'user' and 'content' in msg:
                                prompt_content_to_log = msg['content'][:500] 
                                break
                        if not prompt_content_to_log and len(prompt_messages_list) > 0 and 'content' in prompt_messages_list[-1]:
                             prompt_content_to_log = prompt_messages_list[-1]['content'][:500]
                    logging.info(f"For {lang}, the prompt content (partial): {prompt_content_to_log}... The raw AI output: {quiz_str[:500]}...")
                    quizzes_by_language[lang] = [] 
                    if self.error_notifier and Config.LOG_CHANNEL_ID and 'log' in Config.LOG_CHANNEL_ID:
                        asyncio.run(self.error_notifier.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=f"Quiz JSON Decode Error for {lang}. Prompt (partial): {prompt_content_to_log}... Output: {quiz_str[:500]}..."))
                    continue 
            
            except Exception as e_outer: 
                logging.error(f"An unexpected error occurred while generating quizzes for {lang}: {e_outer}")
                quizzes_by_language[lang] = []
                if self.error_notifier and Config.LOG_CHANNEL_ID and 'log' in Config.LOG_CHANNEL_ID:
                     asyncio.run(self.error_notifier.send_message(chat_id=Config.LOG_CHANNEL_ID['log'], message=f"QuizGenerator: Unexpected error for {lang}: {str(e_outer)}"))
                continue 

        return quizzes_by_language


class QuizVerifier:
    def __init__(self, primary_text_generator: AITextGenerator, verifier_text_generator: AITextGenerator, languages: list = None):
        self.primary_text_generator = primary_text_generator 
        self.verifier_text_generator = verifier_text_generator 
        self.languages = languages if languages is not None else LANGUAGES

    def verify_quizzes(self, questions_by_lang: dict, news_articles: list) -> dict:
        good_questions_final = {language: [] for language in self.languages}
        bad_questions_final = {language: [] for language in self.languages}

        for language in self.languages:
            initial_opinion = questions_by_lang.get(language, [])
            if not initial_opinion:
                logging.warning(f"No initial questions to verify for language: {language}")
                continue

            logging.info(f"Starting verification for {language}. Initial questions: {len(initial_opinion)}")
            tasks_verifier = Tasks(news=news_articles, language=language)
            verification_prompt_list = tasks_verifier.verify(initial_opinion)

            second_opinion_questions = []
            if self.verifier_text_generator:
                gemini_prompt_content = ""
                if verification_prompt_list and isinstance(verification_prompt_list, list) and len(verification_prompt_list) > 0:
                    if 'content' in verification_prompt_list[0]:
                        gemini_prompt_content = verification_prompt_list[0]['content']
                    if len(verification_prompt_list) > 1 and 'content' in verification_prompt_list[1]:
                        gemini_prompt_content += " " + verification_prompt_list[1]['content']
                
                if gemini_prompt_content.strip(): 
                    gemini_messages_list = [{"role": "user", "content": gemini_prompt_content.strip()}]
                    prompt_for_verifier = {"messages": gemini_messages_list}
                    logging.info(f"Sending to verifier_text_generator for {language} (Gemini-like). Prompt based on concatenation of verification_prompt content.")
                    verif_str = self.verifier_text_generator.generate_text(prompt=prompt_for_verifier)
                    if verif_str:
                        try:
                            second_opinion_questions = json.loads(verif_str)
                            if not isinstance(second_opinion_questions, list):
                                logging.warning(f"Second opinion for {language} is not a list. Output: {verif_str[:500]}")
                                second_opinion_questions = [] 
                        except json.JSONDecodeError as e:
                            logging.error(f"JSONDecodeError for second opinion ({language}): {e}. Output: {verif_str[:500]}")
                            second_opinion_questions = []
                    else:
                        logging.warning(f"Second opinion generation failed for {language} (returned None).")
                        second_opinion_questions = []
                else:
                    logging.warning(f"Could not construct prompt for second opinion for {language} from verification_prompt_list content.")
                    second_opinion_questions = []
            else:
                logging.info(f"No verifier_text_generator configured. Skipping second opinion for {language}.")
                second_opinion_questions = []

            third_opinion_questions = []
            if self.primary_text_generator:
                if verification_prompt_list: 
                    prompt_for_primary = {"messages": verification_prompt_list}
                    logging.info(f"Sending to primary_text_generator for {language} (OpenAI-like). Prompt based on Tasks().verify output list.")
                    verif_str_primary = self.primary_text_generator.generate_text(prompt=prompt_for_primary)
                    if verif_str_primary:
                        try:
                            third_opinion_questions = json.loads(verif_str_primary)
                            if not isinstance(third_opinion_questions, list):
                                logging.warning(f"Third opinion for {language} is not a list. Output: {verif_str_primary[:500]}")
                                third_opinion_questions = []
                        except json.JSONDecodeError as e:
                            logging.error(f"JSONDecodeError for third opinion ({language}): {e}. Output: {verif_str_primary[:500]}")
                            third_opinion_questions = []
                    else:
                        logging.warning(f"Third opinion generation failed for {language} (returned None).")
                        third_opinion_questions = []
                else:
                    logging.warning(f"Verification_prompt_list for {language} was empty. Skipping third opinion.")
                    third_opinion_questions = []
            else:
                logging.info(f"No primary_text_generator configured. Skipping third opinion for {language}.")
                third_opinion_questions = []

            for initial_q_dict in initial_opinion:
                if not isinstance(initial_q_dict, dict):
                    logging.warning(f"Skipping non-dict item in initial_opinion for {language}: {initial_q_dict}")
                    continue
                
                q_id = initial_q_dict.get('question_id')
                if q_id is None:
                    logging.warning(f"Skipping question in initial_opinion for {language} due to missing 'question_id': {initial_q_dict}")
                    initial_q_dict['verification_error'] = "Missing question_id in initial"
                    bad_questions_final[language].append(initial_q_dict)
                    continue

                is_good = True 
                if 'options' in initial_q_dict and isinstance(initial_q_dict['options'], list):
                    if len(initial_q_dict['options']) != len(set(initial_q_dict['options'])):
                        logging.warning(f"Q_ID {q_id} ({language}): Duplicate options in initial. Marked as bad.")
                        initial_q_dict['verification_error'] = "Duplicate options in initial"
                        is_good = False
                else:
                    logging.warning(f"Q_ID {q_id} ({language}): Missing or invalid options in initial. Marked as bad.")
                    initial_q_dict['verification_error'] = "Missing/invalid options in initial"
                    is_good = False 

                second_q_match = next((q for q in second_opinion_questions if isinstance(q, dict) and q.get('question_id') == q_id), None)
                third_q_match = next((q for q in third_opinion_questions if isinstance(q, dict) and q.get('question_id') == q_id), None)

                if is_good: 
                    if second_q_match and third_q_match:
                        if not (initial_q_dict.get('correct_option_id') == second_q_match.get('correct_option_id') == third_q_match.get('correct_option_id')):
                            is_good = False
                            initial_q_dict['verification_error'] = "Correct option mismatch (3 opinions)"
                            logging.warning(f"Q_ID {q_id} ({language}): Correct option mismatch (3 opinions). Initial: {initial_q_dict.get('correct_option_id')}, Second: {second_q_match.get('correct_option_id')}, Third: {third_q_match.get('correct_option_id')}")
                    elif second_q_match: 
                        if not (initial_q_dict.get('correct_option_id') == second_q_match.get('correct_option_id')):
                            is_good = False
                            initial_q_dict['verification_error'] = "Correct option mismatch (initial vs second)"
                            logging.warning(f"Q_ID {q_id} ({language}): Correct option mismatch (initial vs second). Initial: {initial_q_dict.get('correct_option_id')}, Second: {second_q_match.get('correct_option_id')}")
                    elif third_q_match: 
                        if not (initial_q_dict.get('correct_option_id') == third_q_match.get('correct_option_id')):
                            is_good = False
                            initial_q_dict['verification_error'] = "Correct option mismatch (initial vs third)"
                            logging.warning(f"Q_ID {q_id} ({language}): Correct option mismatch (initial vs third). Initial: {initial_q_dict.get('correct_option_id')}, Third: {third_q_match.get('correct_option_id')}")
                    else:
                        is_good = False
                        initial_q_dict['verification_error'] = "No other opinions available for verification"
                        logging.warning(f"Q_ID {q_id} ({language}): No other opinions available for verification.")
                
                if is_good:
                    good_questions_final[language].append(initial_q_dict)
                else:
                    bad_questions_final[language].append(initial_q_dict)
            
            logging.info(f"Verification for {language} done. Good: {len(good_questions_final[language])}, Bad: {len(bad_questions_final[language])}")

        return {'good': good_questions_final, 'bad': bad_questions_final}


class ImageGenerator:
    def __init__(self, image_generator_model: AIImageGenerator, languages: list = None):
        self.image_generator_model = image_generator_model
        self.languages = languages if languages is not None else LANGUAGES

    def generate_images_for_topics(self, topics_by_lang: dict) -> dict:
        generated_images_by_lang = {}
        picture_prompt_creator = Picture()

        for language in self.languages:
            # Check if topics exist for the current language and are not empty
            if language in topics_by_lang and topics_by_lang[language]:
                # Use the first topic for image generation prompt
                # The topic itself (e.g., a good quiz question dict) is passed to json.dumps
                first_topic_for_image = topics_by_lang[language][0]
                try:
                    # Serialize the topic dictionary to a JSON string for the prompt
                    topic_json_str = json.dumps(first_topic_for_image)
                    picture_prompt_str = picture_prompt_creator.get_picture_prompt(text=topic_json_str)
                    
                    logging.info(f"Generating image for language '{language}' with topic: {topic_json_str[:200]}...") # Log part of the topic
                    
                    # Call the AIImageGenerator's method
                    # The generate_image method in AIImageGenerator interface returns a PIL Image object or None
                    generated_image: Image.Image = self.image_generator_model.generate_image(prompt=picture_prompt_str)
                    
                    if generated_image:
                        generated_images_by_lang[language] = generated_image
                        logging.info(f"Successfully generated image for language '{language}'.")
                    else:
                        logging.warning(f"Image generation returned None for language '{language}' with topic: {topic_json_str[:200]}.")
                
                except json.JSONEncodeError as e:
                    logging.error(f"Failed to serialize topic to JSON for image prompt ({language}): {e}. Topic: {first_topic_for_image}")
                except Exception as e:
                    # Catch any other errors during image generation for a specific language
                    logging.error(f"Error generating image for language '{language}': {e}. Topic: {first_topic_for_image}")
            else:
                logging.info(f"No topics provided for image generation in language '{language}', or topic list was empty. Skipping.")
        
        return generated_images_by_lang
