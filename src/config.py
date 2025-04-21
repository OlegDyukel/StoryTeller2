import os

class Config:
    SECRET_KEY = os.urandom(44)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    LOG_CHANNEL_ID = {'log': os.getenv('LOG_CHANNEL_ID')}
    CHANNEL_ID = {'english': os.getenv('ENG_CHANNEL_ID'), 'spanish': os.getenv('ESP_CHANNEL_ID')}


class Parameter:
    N_options = 5
    SCHEDULE = {'Monday': 'grammar',
                'Tuesday': 'word',
                'Wednesday': 'grammar',
                'Thursday': 'word',
                'Friday': 'grammar',
                'Saturday': 'word',
                'Sunday': 'grammar'}