import random
import datetime

n_questions = 4
LANGUAGE = 'English'
CATEGORIES = ['Sport', 'Disaster', 'Innovation', 'Science', 'Environment', 'Technology',
              'Healthcare', 'Politics']
REGIONS = ['Europe', 'Asia', 'Africa', 'North America', 'South America', 'India', 'Russia']
TOPICS = ['Present and past', 'Present perfect and past', 'Future', 'Modals', 'If and wish',
          'Passive', 'Reported speech', 'Questions and auxiliary verbs', '-ing and the infinitive',
          'Articles and nouns', 'Pronouns and determiners', 'Relative clauses', 'Prepositions',
          'Adjectives and adverbs', 'Conjunctions and prepositions', 'Phrasal verbs', 'Organising information',
          'Adverbial clauses and conjunctions', 'Pronouns, substitution and leaving out words',
          'Relative clauses and other types of clause', 'Articles, determiners and quantifiers',
          'Verb complementation: what follows verbs', 'Linking verbs, passives, questions',
          'Modals and semi-modals']

class News:
    def __init__(self):
        self.date = datetime.datetime.today().date()
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
        self.news_categories = random.sample(CATEGORIES, k=n_questions)
        self.news_regions = random.sample(REGIONS, k=n_questions)
        self.news_category_mapping = []
        for i in range(n_questions):
            d = {'news_id': i+1, 'category': self.news_categories[i], 'region': self.news_regions[i]}
            self.news_category_mapping.append(d)

    def get_prompt(self) -> list:
        system_prompt = "You are a news generator."

        prompt = f"""
            Please generate {n_questions} diverse news stories with IDs, categories, regions, and texts 
            as of {self.date} day
            in the following JSON array without any additional text:
            
            [
                {{"id": 1, "category": "sport", "region": "world", "text": "something ..."}},
                ...
            ]
            
            Here is an example to illustrate the format: {self.news_examples}
            
            Constraints:
            News should be related to the following categories and regions:
            {self.news_category_mapping}
            
            The text of news should be a narrative and easily perceived story.
            
            The text of news can be 1, 2 or maximum 3 sentences.
            
            Ensure that each entry follows this structure with relevant and updated information as of {self.date}.
            """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        return messages


class Tasks:
    def __init__(self, news: list):
        super().__init__()
        self.question_examples = [
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
        ]
        self.grammar_topics = random.sample(TOPICS, k=n_questions)
        self.question_grammar_news_mapping = []
        for i in range(n_questions):
            d = {'question_id': i+1, 'grammar_topic': self.grammar_topics[i], 'news': news[i]['text']}
            self.question_grammar_news_mapping.append(d)

    def get_prompt(self) -> list:
        system_prompt = f"""
        You are a language learning quiz generator in {LANGUAGE}. 
        Your task is to create multiple-choice questions 
        focused on {LANGUAGE} grammar and vocabulary. 
        """

        prompt = f"""
        Please generate a list of {n_questions} questions with multiple-choice options and indicate 
        the correct option for each question. 
        Each item of the list should be structured as a dictionary with the following 
        keys: `question_id`, `grammar_topic`, `question`, `options`, `correct_option_id` and `explanation`. 
        The `options` key should contain 
        a list of possible answers, and `correct_option_id` should be the index of the 
        correct answer in the `options` list (0-indexed). The correct answer should be only one.
        
        Please output the result as a JSON array without any additional text.
        The output should have the following format:
        
        [
            {{
              "question_id": <ID of the question (1, 2, 3, 4, ...)>,
              "grammar_topic": "The grammar topic the question addresses",
              "question": "The incomplete sentence requiring a correct option.",
              "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
              "correct_option_id": <ID of the correct option (0, 1, 2, or 3)>,
              "explanation": " a short explanation of the correct answer "
            }},
            ...
        ]
        
        Here is an example to illustrate the format: {self.question_examples}
          
        Questions should be related to the following grammar topics and news:
        {self.question_grammar_news_mapping}
        
        Please generate similar questions in this format, ensuring the options are varied and the 
        correct option is accurately identified.
        Poll question length must not exceed 300.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        return messages
