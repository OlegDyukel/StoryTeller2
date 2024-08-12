import os

class Config:
    SECRET_KEY = os.urandom(44)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHANNEL_ID = "@english_quizzes_ai"  # os.getenv('TELEGRAM_CHANNEL_ID')
