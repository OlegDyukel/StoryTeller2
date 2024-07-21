from openai_api import OpenaiAPI
from config import Config


if __name__ == "__main__":
    prompt = "Tell me a story about a brave knight."
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a story about a brave knight."}
    ]
    openai = OpenaiAPI(
        api_key=Config.OPENAI_API_KEY,
        model='gpt-3.5-turbo'
    )
    result = openai.generate_response(messages=messages)
    if result:
        print(f"Generated Text: {result}")
    else:
        print("Failed to generate text.")
