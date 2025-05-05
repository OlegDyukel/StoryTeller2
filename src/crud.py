from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Session, ForeignWord
import csv
from sqlalchemy import func
import random


def add_word(word, language, meaning=None, context=None, word_type=None, example=None):
    session = Session()
    new_word = ForeignWord(
        word=word, language=language, meaning=meaning, context=context, word_type=word_type, example=example
    )
    session.add(new_word)
    session.commit()
    session.close()


def get_words(language=None):
    session = Session()
    query = session.query(ForeignWord)
    if language:
        query = query.filter(func.lower(ForeignWord.language) == language.lower())
    words = query.all()
    session.close()
    return words


def get_random_words(language, count=5):
    """Retrieves a specified number of random words for a given language."""
    session = Session()
    try:
        words = session.query(ForeignWord)\
                      .filter(func.lower(ForeignWord.language) == language.lower())\
                      .order_by(func.random()) \
                      .limit(count)\
                      .all()
        return words
    except Exception as e:
        print(f"An error occurred while fetching random words: {e}")
        return [] # Return empty list on error
    finally:
        session.close()


def import_words_from_csv(csv_filepath):
    """Reads words from a CSV file and bulk inserts them into the database."""
    session = Session()
    words_to_insert = []
    try:
        with open(csv_filepath, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Check if required columns exist
            required_columns = {'language', 'word'}
            if not required_columns.issubset(reader.fieldnames):
                print(f"Error: CSV file must contain at least the columns: {', '.join(required_columns)}")
                return
                
            for row in reader:
                # Map CSV columns to ForeignWord attributes, handling potential missing optional columns
                word_data = {
                    'language': row.get('language'),
                    'word': row.get('word'),
                    'meaning': row.get('meaning', None) or None, # Ensure empty strings become None
                    'context': row.get('context', None) or None,
                    'word_type': row.get('word_type', None) or None,
                    'example': row.get('example', None) or None
                }
                # Skip rows where essential data (word, language) is missing
                if word_data['word'] and word_data['language']:
                     words_to_insert.append(word_data)
                else:
                    print(f"Skipping row due to missing word or language: {row}")

        if words_to_insert:
            session.bulk_insert_mappings(ForeignWord, words_to_insert)
            session.commit()
            print(f"Successfully imported {len(words_to_insert)} words from {csv_filepath}")
        else:
            print("No valid words found in CSV to import.")
            
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_filepath}")
    except Exception as e:
        session.rollback() # Rollback in case of any error during processing
        print(f"An error occurred during import: {e}")
    finally:
        session.close()
