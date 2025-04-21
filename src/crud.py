from models import Session, ForeignWord


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
        query = query.filter(ForeignWord.language == language)
    words = query.all()
    session.close()
    return words
