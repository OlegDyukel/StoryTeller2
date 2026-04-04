import random
import datetime
import json
from typing import Optional

N_QUESTIONS = 4
N_OPTIONS = 4
CATEGORIES = ['Sport', 'Disaster', 'Innovation', 'Science', 'Environment', 'Technology',
              'Healthcare', 'Politics']
REGIONS = ['Europe', 'Asia', 'Africa', 'North America', 'South America', 'USA', 'China and India',
           'Oceania', 'Post-Soviet states']
ENGLISH_GRAMMAR_TOPICS = [
    'Present and past', 'Present perfect and past', 'Future', 'Modals', 'If and wish',
    'Passive', 'Reported speech', 'Questions and auxiliary verbs', '-ing and the infinitive',
    'Articles and nouns', 'Pronouns and determiners', 'Relative clauses', 'Prepositions',
    'Adjectives and adverbs', 'Conjunctions and prepositions', 'Phrasal verbs',
    'Adverbial clauses and conjunctions', 'Pronouns, substitution and leaving out words',
    'Relative clauses and other types of clause', 'Articles, determiners and quantifiers',
    'Verb complementation: what follows verbs', 'Linking verbs, passives, questions',
    'Modals and semi-modals']

SPANISH_GRAMMAR_TOPICS = [
    "Present Tense (Presente)", "Past Tenses: Preterite and Imperfect (Pretérito y Imperfecto)",
    "Present Perfect and Past Perfect (Pretérito Perfecto y Pluscuamperfecto)", "Future Tense (Futuro)",
    "Conditional Tense (Condicional)", "Modal Verbs (Verbos Modales)",
    "Subjunctive Mood (Presente de Subjuntivo)", "Commands/Imperative (Imperativo)", "Passive Voice (Voz Pasiva)",
    "Reported Speech (Estilo Indirecto)", "Questions and Question Words (Interrogativos)",
    "Gerunds and Infinitives (Gerundios e Infinitivos)",
    "Definite and Indefinite Articles (Artículos Definidos e Indefinidos)", "Nouns and Gender (Sustantivos y Género)",
    "Pronouns (Pronombres)", "Adjectives (Adjetivos)", "Adverbs (Adverbios)", "Prepositions (Preposiciones)",
    "Conjunctions (Conjunciones)", "Relative Clauses (Oraciones de Relativo)",
    "Phrasal Verbs and Verb Phrases (Verbos Frasales y Frases Verbales)",
    "Direct and Indirect Object Pronouns (Pronombres de Objeto Directo e Indirecto)",
    "Reflexive Verbs (Verbos Reflexivos)", "Comparatives and Superlatives (Comparativos y Superlativos)",
    "Tense Agreement (Concordancia de Tiempos)", "Ser vs. Estar (Usage of 'Ser' and 'Estar')",
    "Por vs. Para (Usage of 'Por' and 'Para')", "Impersonal Expressions (Expresiones Impersonales)",
    "Negation (Negación)", "Word Order (Orden de las Palabras)"]

PICTURE_STYLES = ['pixel art', 'vivid, lively', 'pixar/disney', 'realistic photography',
                  'anime/manga', 'watercolor and traditional art', 'cyberpunk and futuristic aesthetics',
                  'minimalistic and flat', 'fantasy and mythological', 'surreal and abstract']

TOPICS = {'english': ENGLISH_GRAMMAR_TOPICS, 'spanish': SPANISH_GRAMMAR_TOPICS}

JSON_CONSTRAINTS = """
Your response must be in JSON format, without using code blocks, additional text and the surrounding backticks.
Keys, property names and string values must be enclosed in double quotes,
in order to json.loads() function can process the response properly.
"""

MessageList = list[dict[str, str]]


class News:
    def __init__(self):
        self.news_format = [{"id": 1, "category": "sport", "region": "world", "text": "something ..."}, ]
        self.news_examples = [
            {
                "id": 1,
                "category": "sport",
                "region": "USA",
                "text": "The Los Angeles Lakers have won the 2024 NBA Championship, defeating the Boston Celtics in a thrilling seven-game series. This marks their 18th title in franchise history, tying them with the Celtics for the most championships in NBA history."
            },
            {
                "id": 2,
                "category": "science",
                "region": "Europe",
                "text": "A team of European scientists has successfully developed a new drug that significantly slows the progression of Alzheimer's disease. The breakthrough medication has shown promising results in clinical trials, offering hope to millions affected by the condition."
            },
            {
                "id": 3,
                "category": "environment",
                "region": "Australia",
                "text": "Australia has announced the creation of a new marine sanctuary in the Great Barrier Reef. This protected area aims to conserve biodiversity and restore coral ecosystems damaged by climate change and human activity."
            },
        ]
        self.news_categories = random.sample(CATEGORIES, k=N_QUESTIONS)
        self.news_regions = random.sample(REGIONS, k=N_QUESTIONS)
        self.news_category_mapping = [
            {"news_id": i + 1, "category": self.news_categories[i], "region": self.news_regions[i]}
            for i in range(N_QUESTIONS)
        ]

    def get_prompt(self) -> MessageList:
        date = datetime.datetime.today().date()
        system_prompt = "You are a news generator."

        prompt = f"""
            Please generate {N_QUESTIONS} diverse news stories with IDs, categories, regions, and texts
            as of {date} day
            in the following JSON array without any additional text: {json.dumps(self.news_format)}
            Here is an example to illustrate the format: {json.dumps(self.news_examples)}

            Constraints:
            News should be related to the following categories and regions:
            {json.dumps(self.news_category_mapping)}

            The text of news should be a narrative and easily perceived story.
            The text of the news can be 1, 2 or a maximum of 3 sentences and no more than 1000 characters.
            Ensure that each entry follows this structure with relevant and updated information as of {date}.

            Return only a valid JSON array with exactly {N_QUESTIONS} items, no prologue/epilogue text,
            no code fences, and no trailing commas. If a string needs quotes inside, escape them properly.

            {JSON_CONSTRAINTS}
            """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

    def get_news_story_prompt(self) -> MessageList:
        system_prompt = "You are a news generator."
        prompt = """
            Please provide one of the most significant news story from this past week
            that has had a significant impact on the world.
            Constraints:
            The text of news should be a narrative and easily perceived story.
            The text of the news can be 1, 2 or a maximum of 3 sentences and no more than 1000 characters.
            """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]


class Tasks:
    def __init__(self, news: list[dict], language: str, word: Optional[str] = None):
        assert len(news) >= N_QUESTIONS, f"Expected at least {N_QUESTIONS} news items, got {len(news)}"

        self.language = language
        if word is None:
            self.word_phrase = 'definition of a word (phrasal verbs or other intermediate level words).'
        else:
            self.word_phrase = f'a <word>{word}</word> definition. The definition should be succinct: from 2 to 10 words.'
        self.question_format = [
            {
                "question_id": "<ID of the question (1, 2, 3, 4, ...)>",
                "grammar_topic": "The grammar topic the question addresses",
                "question": "The incomplete sentence requiring a correct option.",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "correct_option_id": "<ID of the correct option (0, 1, 2, or 3)>",
                "explanation": " a short explanation of the correct answer "
            },
        ]
        self.question_example = [
            {
                "question_id": 1,
                "grammar_topic": "Prepositions",
                "question": "Alice travelled ___ 9:20 train, which arrived at 9:55.",
                "options": ["in the", "by a", "by the", "on the"],
                "correct_option_id": 3,
                "explanation": "The preposition on is typically used to indicate traveling by a specific mode of transport like a train, bus, or plane, especially when referring to a specific scheduled service."
            },
            {
                "question_id": 2,
                "grammar_topic": "Questions and auxiliary verbs",
                "question": "Do you know where ___ ?",
                "options": ["Bob have gone", "Bob has gone", "have Bob gone", "has gone Bob"],
                "correct_option_id": 1,
                "explanation": "Bob has gone: This is correct because has is the correct auxiliary verb for third-person singular subjects like Bob"
            },
            {
                "question_id": 3,
                "grammar_topic": "Organising information",
                "question": " ___ people trying to get into the party.",
                "options": ["There were too much", "There was too many", "It was too many", "There were too many"],
                "correct_option_id": 3,
                "explanation": "There were too many: This is correct because were matches the plural noun people, and many is the appropriate quantifier for countable nouns"
            },
            {
                "question_id": 4,
                "grammar_topic": "Phrasal verbs",
                "question": "Turn down is ...",
                "options": ["to reduce the volume or intensity of something",
                            "to stop trying to do something or to quit",
                            "to reject or refuse something, such as an offer or invitation",
                            "to meet someone unexpectedly or by chance"],
                "correct_option_id": 2,
                "explanation": "Example: I had to turn down the job offer because it wasn't the right fit for me."
            },
        ]
        self.verification_format = [{"question_id": "1 or 2 or 3 or 4 (id of a given question)",
                                     "correct_options": ["a list of correct options"]}]
        self.verification_example = [{"question_id": 1, "correct_options": ["on the"]},
                                     {"question_id": 2, "correct_options": ["Bob has gone"]},
                                     {"question_id": 3, "correct_options": ["There were too many people"]},
                                     {"question_id": 4, "correct_options":
                                         ["to reduce the volume or intensity of something",
                                          "to reject or refuse something, such as an offer or invitation"]}]
        self.grammar_topics = random.sample(TOPICS[self.language], k=N_QUESTIONS)
        self.correct_answers = [random.randint(0, N_OPTIONS - 1) for _ in range(N_QUESTIONS)]
        self.question_grammar_news_mapping = [
            {
                "question_id": i + 1,
                "grammar_topic": self.grammar_topics[i],
                "news": news[i]['text'],
                "correct_answer_id": self.correct_answers[i],
            }
            for i in range(N_QUESTIONS)
        ]

    def get_correct_answers(self) -> list[dict]:
        return self.question_grammar_news_mapping

    def get_prompt(self) -> MessageList:
        system_prompt = f"""
        You are a language learning quiz generator in {self.language}.
        Your task is to create multiple-choice questions
        focused on {self.language} grammar and vocabulary.
        """

        # Build per-question instructions dynamically
        m0 = self.question_grammar_news_mapping[0]
        vocab_instruction = f"""
        The first question should be about {self.word_phrase}. Please check whether the word or phrase exists
        and is spelled correctly, and make corrections if needed.
        Then please suggest one correct definition and {N_OPTIONS - 1} incorrect definitions then please put
        the correct option to {m0['correct_answer_id']} element of the list with options.
        The question length must not exceed 250 characters.
        Example: {json.dumps(self.question_example[-1])}
        """

        grammar_instructions = []
        ordinals = ["second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"]
        for i in range(1, N_QUESTIONS):
            m = self.question_grammar_news_mapping[i]
            grammar_instructions.append(
                f"The {ordinals[i - 1]} question should be a {m['grammar_topic']} grammar question "
                f"and related to <news>{m['news']}</news> news. And please put the correct option to "
                f"{m['correct_answer_id']} element of the list with options. Add an "
                f"explanation of the correct option. The question length must not exceed 250 characters."
            )

        prompt = f"""
        Please generate a list of {N_QUESTIONS} questions with multiple-choice options and indicate
        the correct option for each question.
        Each item of the list should be structured as a dictionary with the following
        keys: `question_id`, `grammar_topic`, `question`, `options`, `correct_option_id` and `explanation`.
        The `options` key should contain
        a list of possible answers, and `correct_option_id` should be the index (integer) of the
        correct answer in the `options` list (0-indexed). The correct answer should be only one.

        The output should have the following format:
        {json.dumps(self.question_format)}
        Here is an example to illustrate the format: {json.dumps(self.question_example)}

        {vocab_instruction}

        {chr(10).join(grammar_instructions)}

        {JSON_CONSTRAINTS}
        Please generate similar questions in this format, ensuring the options are varied and the
        correct option is accurately identified.
        The questions and answers should be in {self.language}.
        """

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

    def verify(self, questions: list[dict]) -> MessageList:
        assert len(questions) >= N_QUESTIONS, f"Expected at least {N_QUESTIONS} questions, got {len(questions)}"

        system_prompt = f"""
        You are a professional linguist and an {self.language} teacher at university.
        """

        def _format_task(idx: int, q: dict) -> str:
            return (f"Task {idx + 1}: {q['question']} \n"
                    f"What answer/answers is/are correct? {json.dumps(q['options'])}")

        example_tasks = "\n".join(_format_task(i, self.question_example[i])
                                  for i in range(len(self.question_example)))
        actual_tasks = "\n".join(_format_task(i, questions[i])
                                 for i in range(N_QUESTIONS))

        prompt = f"""
            You will receive {N_QUESTIONS} language tasks related to grammar and vocabulary,
            with {N_OPTIONS} possible answers for each task. The possible answers are in the list.
            Your task is to define which options are correct.
            There might be 0, 1, 2, 3 or even {N_OPTIONS} correct/possible answers.
            You will receive structured enumerated tasks and you need to return a result in JSON format.
            The input and output have the following structure:
            EXAMPLE OF INPUT:
            {example_tasks}
            OUTPUT FORMAT:
            {json.dumps(self.verification_format)}
            EXAMPLE OF OUTPUT:
            {json.dumps(self.verification_example)}.
            So following the instructions above please provide answers to the following tasks:
            {actual_tasks}

            {JSON_CONSTRAINTS}
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]


class QuizDefinitions:
    def __init__(self, language: str, word_list: list[str]):
        self.language = language
        self.word_list = word_list
        self.definition_format = {"word1": "definition1", "word2": "definition2"}

    def get_prompt(self) -> str:
        """Generates the prompt string to request definitions for the word list."""
        prompt = f"""Provide short, distinct definitions for the following {self.language} words.
        Return the response ONLY as a valid JSON object where keys are the words and values are the definitions.
        Example format: {json.dumps(self.definition_format)}
        Words: {', '.join(self.word_list)}
        """
        return prompt


class Picture:
    def get_picture_prompt(self, text: str) -> str:
        style = random.choice(PICTURE_STYLES)
        return (
            f"You are an artist working at Pixar or Disney Studios.\n"
            f"Please create a symbolic or thematic illustration that captures the essence of the word/phrase/text "
            f"in a {style} style. The text can be both a simple text and a quiz task in a json-like format:\n"
            f"<content>{text}</content>.\n"
            f"If you aren't able to generate such an image because it did not align with the content policy "
            f"guidelines, please do a symbolic or thematic illustration that relates to one of the most "
            f"significant news story from this past week that had a significant impact on the world."
        )
