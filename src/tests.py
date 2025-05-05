from crud import get_words, import_words_from_csv, get_random_words
import os

if __name__ == "__main__":
    # --- Test 0: Get environment variables --- 
    database_url = os.environ.get('DATABASE_URL')
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    print("Database URL:", database_url)
    print("Gemini API Key:", gemini_api_key)
    print("OpenAI API Key:", openai_api_key)
    print("Telegram Bot Token:", telegram_bot_token)

    # --- Test 1: Get all words and display first 5 --- 
    print("--- Testing get_words() --- ")
    all_words = get_words()

    if all_words:
        print(f"Total words found: {len(all_words)}")
        print("\nFirst 5 words:")
        for i, word_obj in enumerate(all_words[:5]):
            print(f"  - ID: {word_obj.id}, Lang: {word_obj.language}, Word: {word_obj.word}, Meaning: {word_obj.meaning}")
    else:
        print("No words found in the database.")

    # --- Test 2: Get words by specific language (example) --- 
    print("\n--- Testing get_words(language='spanish') --- ")
    data = get_words(language='spanish') 

    if data:
        print(f"Found {len(data)} words. First one:")
        word_obj = data[0]
        print(f"  - ID: {word_obj.id}, Lang: {word_obj.language}, Word: {word_obj.word}, Meaning: {word_obj.meaning}")
    else:
        print("No words found for the language. Check case sensitivity or data.")

    print("\n--- Test Script Finished ---")

    # --- Test 3: Get random words --- 
    print("\n--- Testing get_random_words() ---")
    random_english = get_random_words('english', 5)
    print("\n5 Random English words:")
    if random_english:
        for word_obj in random_english:
            print(f"  - ID: {word_obj.id}, Word: {word_obj.word}")
    else:
        print("  No English words found or error occurred.")

    random_spanish = get_random_words('spanish', 5)
    print("\n5 Random Spanish words:")
    if random_spanish:
        for word_obj in random_spanish:
            print(f"  - ID: {word_obj.id}, Word: {word_obj.word}")
    else:
        print("  No Spanish words found or error occurred.")


    # csv_file_path = 'data/words.csv' 
    # Note: The import runs only when the script is executed directly.
    # If the database is already populated, you might comment out the import line below
    # to prevent re-importing data every time the script is run directly.
    # print(f"Attempting to import words from: {csv_file_path}")
    # import_words_from_csv(csv_file_path)
    # print("CRUD script finished. Database setup/import might have run if uncommented.") # Placeholder message
