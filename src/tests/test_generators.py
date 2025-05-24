import unittest
from unittest.mock import MagicMock, patch, call
import json # For creating expected output and checking error messages

from src.generators import NewsGenerator, QuizGenerator, QuizVerifier, LANGUAGES # Added QuizVerifier and LANGUAGES
from src.interfaces import AITextGenerator, MessagingService
# News from src.prompts is used internally by NewsGenerator, so we'll patch it.
# from src.prompts import News 
from src.config import Config # For Config.LOG_CHANNEL_ID


class TestNewsGenerator(unittest.TestCase):

    def setUp(self):
        # Common mock for AITextGenerator
        self.mock_text_generator = MagicMock(spec=AITextGenerator)
        
        # Common mock for MessagingService (error_notifier)
        self.mock_error_notifier = MagicMock(spec=MessagingService)

        # Default fixed prompt from News().get_prompt()
        self.fixed_news_prompt_list = [
            {"role": "system", "content": "System message for news"},
            {"role": "user", "content": "User instruction for news."}
        ]
        # Based on NewsGenerator's logic, it concatenates content of first two messages from news_prompt_list
        # and wraps it in {"role": "user", "content": concatenated_content}
        # then passes {"messages": [this_dict]} to the text_generator
        concatenated_content = self.fixed_news_prompt_list[0]['content'] + " " + self.fixed_news_prompt_list[1]['content']
        self.expected_prompt_to_ai = {"messages": [{"role": "user", "content": concatenated_content.strip()}]}


    @patch('src.generators.News') # Patching News where it's imported in generators.py
    @patch('src.generators.asyncio.run') # Patch asyncio.run for error notifier
    def test_get_news_success(self, mock_asyncio_run, MockNews):
        # Arrange
        # Configure the mock for News().get_prompt()
        MockNews.return_value.get_prompt.return_value = self.fixed_news_prompt_list
        
        expected_news_output_str = '[{"id": 1, "text": "Test News Story"}]'
        expected_news_output_list = [{"id": 1, "text": "Test News Story"}]
        self.mock_text_generator.generate_text.return_value = expected_news_output_str
        
        news_generator = NewsGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier
        )

        # Act
        news_list = news_generator.get_news()

        # Assert
        MockNews.return_value.get_prompt.assert_called_once()
        self.mock_text_generator.generate_text.assert_called_once_with(prompt=self.expected_prompt_to_ai)
        self.assertEqual(news_list, expected_news_output_list)
        self.mock_error_notifier.send_message.assert_not_called()
        mock_asyncio_run.assert_not_called() # Ensure asyncio.run wasn't called for notifications

    @patch('src.generators.News')
    @patch('src.generators.asyncio.run')
    @patch.dict(Config.LOG_CHANNEL_ID, {'log': 'test_log_channel_id'}, clear=True)
    def test_get_news_json_decode_error(self, mock_asyncio_run, MockNews):
        # Arrange
        MockNews.return_value.get_prompt.return_value = self.fixed_news_prompt_list
        
        invalid_json_output = "not a valid json string"
        self.mock_text_generator.generate_text.return_value = invalid_json_output
        
        news_generator = NewsGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier
        )

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            news_generator.get_news()
        
        self.assertIn("Failed to get news in JSON format from AI", str(context.exception))
        MockNews.return_value.get_prompt.assert_called_once()
        self.mock_text_generator.generate_text.assert_called_once_with(prompt=self.expected_prompt_to_ai)
        
        mock_asyncio_run.assert_called_once()
        args, kwargs = mock_asyncio_run.call_args
        call_args = args[0].call_args 
        self.assertEqual(call_args.kwargs['chat_id'], 'test_log_channel_id')
        self.assertIn("News JSON Decode Error", call_args.kwargs['message'])
        self.assertIn(invalid_json_output[:1000], call_args.kwargs['message'])


    @patch('src.generators.News')
    @patch('src.generators.asyncio.run')
    @patch.dict(Config.LOG_CHANNEL_ID, {'log': 'test_log_channel_id'}, clear=True)
    def test_get_news_ai_failure_returns_none(self, mock_asyncio_run, MockNews):
        # Arrange
        MockNews.return_value.get_prompt.return_value = self.fixed_news_prompt_list
        self.mock_text_generator.generate_text.return_value = None 
        news_generator = NewsGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier
        )

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            news_generator.get_news()
            
        self.assertIn("Failed to generate news text: AI returned None", str(context.exception))
        MockNews.return_value.get_prompt.assert_called_once()
        self.mock_text_generator.generate_text.assert_called_once_with(prompt=self.expected_prompt_to_ai)
        mock_asyncio_run.assert_called_once()
        args, _ = mock_asyncio_run.call_args
        call_args = args[0].call_args
        self.assertEqual(call_args.kwargs['chat_id'], 'test_log_channel_id')
        self.assertIn("NewsGenerator: AI text_generator returned None", call_args.kwargs['message'])

    @patch('src.generators.News')
    @patch('src.generators.asyncio.run')
    @patch.dict(Config.LOG_CHANNEL_ID, {'log': 'test_log_channel_id'}, clear=True)
    def test_get_news_ai_returns_not_a_list(self, mock_asyncio_run, MockNews):
        # Arrange
        MockNews.return_value.get_prompt.return_value = self.fixed_news_prompt_list
        not_a_list_json = '{"id": 1, "text": "This is a dict, not a list"}'
        self.mock_text_generator.generate_text.return_value = not_a_list_json
        news_generator = NewsGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier
        )

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            news_generator.get_news()
            
        self.assertIn("Generated news is not a list", str(context.exception))
        MockNews.return_value.get_prompt.assert_called_once()
        self.mock_text_generator.generate_text.assert_called_once_with(prompt=self.expected_prompt_to_ai)
        mock_asyncio_run.assert_called_once()
        args, _ = mock_asyncio_run.call_args
        call_args = args[0].call_args
        self.assertEqual(call_args.kwargs['chat_id'], 'test_log_channel_id')
        self.assertIn("NewsGenerator: Generated news is not a list", call_args.kwargs['message'])
        self.assertIn(not_a_list_json[:1000], call_args.kwargs['message'])

    @patch('src.generators.News')
    def test_get_news_no_error_notifier(self, MockNews):
        # Arrange
        MockNews.return_value.get_prompt.return_value = self.fixed_news_prompt_list
        self.mock_text_generator.generate_text.return_value = "invalid json"
        news_generator_no_notifier = NewsGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=None 
        )
        # Act & Assert
        with self.assertRaises(ValueError):
            news_generator_no_notifier.get_news()
        self.mock_error_notifier.send_message.assert_not_called() 

    @patch('src.generators.News')
    @patch('src.generators.asyncio.run') 
    @patch.dict(Config.LOG_CHANNEL_ID, {}, clear=True) 
    def test_get_news_json_decode_error_log_channel_not_configured(self, mock_asyncio_run, MockNews):
        # Arrange
        MockNews.return_value.get_prompt.return_value = self.fixed_news_prompt_list
        self.mock_text_generator.generate_text.return_value = "invalid json"
        news_generator = NewsGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier
        )
        # Act & Assert
        with self.assertRaises(ValueError):
            news_generator.get_news()
        self.mock_error_notifier.send_message.assert_not_called()
        mock_asyncio_run.assert_not_called()


class TestQuizGenerator(unittest.TestCase):

    def setUp(self):
        self.mock_text_generator = MagicMock(spec=AITextGenerator)
        self.mock_error_notifier = MagicMock(spec=MessagingService)
        self.sample_news_list = [{'id': 1, 'title': 'Test News 1', 'text': 'Content of news 1.'}]
        self.fixed_task_prompt_list = [{"role": "user", "content": "Fixed quiz prompt based on news and word."}]
        self.expected_prompt_to_ai_quizzes = {"messages": self.fixed_task_prompt_list}

    @patch('src.generators.Tasks')
    @patch('src.generators.get_random_words')
    @patch('src.generators.asyncio.run')
    def test_generate_quizzes_success(self, mock_asyncio_run, mock_get_random_words, MockTasks):
        # Arrange
        mock_get_random_words.return_value = [MagicMock(word='testword')]
        MockTasks.return_value.get_prompt.return_value = self.fixed_task_prompt_list
        
        expected_quiz_output_str = '[{"question_id": 1, "question": "Q1", "options": ["A", "B"], "correct_option_id": 0, "explanation": "Expl"}]'
        expected_quiz_output_list = json.loads(expected_quiz_output_str)
        self.mock_text_generator.generate_text.return_value = expected_quiz_output_str
        
        quiz_generator = QuizGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier,
            languages=['english']
        )

        # Act
        quizzes_by_lang = quiz_generator.generate_quizzes(news=self.sample_news_list)

        # Assert
        mock_get_random_words.assert_called_once_with('english', 1)
        MockTasks.assert_called_once_with(news=self.sample_news_list, language='english', word='testword')
        MockTasks.return_value.get_prompt.assert_called_once()
        self.mock_text_generator.generate_text.assert_called_once_with(prompt=self.expected_prompt_to_ai_quizzes)
        self.assertIn('english', quizzes_by_lang)
        self.assertEqual(quizzes_by_lang['english'], expected_quiz_output_list)
        self.mock_error_notifier.send_message.assert_not_called()
        mock_asyncio_run.assert_not_called()

    @patch('src.generators.Tasks')
    @patch('src.generators.get_random_words')
    @patch('src.generators.asyncio.run')
    @patch.dict(Config.LOG_CHANNEL_ID, {'log': 'test_log_channel_id'}, clear=True)
    def test_generate_quizzes_json_decode_error(self, mock_asyncio_run, mock_get_random_words, MockTasks):
        # Arrange
        mock_get_random_words.return_value = [MagicMock(word='testword')]
        MockTasks.return_value.get_prompt.return_value = self.fixed_task_prompt_list
        
        invalid_json_output = "not valid json"
        self.mock_text_generator.generate_text.return_value = invalid_json_output
        
        quiz_generator = QuizGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier,
            languages=['english']
        )

        # Act
        quizzes_by_lang = quiz_generator.generate_quizzes(news=self.sample_news_list)

        # Assert
        self.assertEqual(quizzes_by_lang['english'], []) # Expect empty list on error
        mock_asyncio_run.assert_called_once()
        args, _ = mock_asyncio_run.call_args
        call_args = args[0].call_args
        self.assertEqual(call_args.kwargs['chat_id'], 'test_log_channel_id')
        self.assertIn("Quiz JSON Decode Error for english", call_args.kwargs['message'])
        self.assertIn(invalid_json_output[:500], call_args.kwargs['message']) 

    @patch('src.generators.Tasks')
    @patch('src.generators.get_random_words')
    @patch('src.generators.asyncio.run')
    @patch.dict(Config.LOG_CHANNEL_ID, {'log': 'test_log_channel_id'}, clear=True)
    def test_generate_quizzes_ai_failure_returns_none(self, mock_asyncio_run, mock_get_random_words, MockTasks):
        # Arrange
        mock_get_random_words.return_value = [MagicMock(word='testword')]
        MockTasks.return_value.get_prompt.return_value = self.fixed_task_prompt_list
        self.mock_text_generator.generate_text.return_value = None 
        
        quiz_generator = QuizGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier,
            languages=['english']
        )
        # Act
        quizzes_by_lang = quiz_generator.generate_quizzes(news=self.sample_news_list)
        # Assert
        self.assertEqual(quizzes_by_lang['english'], [])
        mock_asyncio_run.assert_called_once()
        args, _ = mock_asyncio_run.call_args
        call_args = args[0].call_args
        self.assertEqual(call_args.kwargs['chat_id'], 'test_log_channel_id')
        self.assertIn("QuizGenerator: AI text_generator returned None for english", call_args.kwargs['message'])

    @patch('src.generators.Tasks')
    @patch('src.generators.get_random_words')
    @patch('src.generators.asyncio.run')
    @patch.dict(Config.LOG_CHANNEL_ID, {'log': 'test_log_channel_id'}, clear=True)
    def test_generate_quizzes_ai_returns_not_a_list(self, mock_asyncio_run, mock_get_random_words, MockTasks):
        # Arrange
        mock_get_random_words.return_value = [MagicMock(word='testword')]
        MockTasks.return_value.get_prompt.return_value = self.fixed_task_prompt_list
        not_a_list_json = '{"key": "not a list"}'
        self.mock_text_generator.generate_text.return_value = not_a_list_json
        quiz_generator = QuizGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier,
            languages=['english']
        )
        # Act
        quizzes_by_lang = quiz_generator.generate_quizzes(news=self.sample_news_list)
        # Assert
        self.assertEqual(quizzes_by_lang['english'], [])
        mock_asyncio_run.assert_called_once()
        args, _ = mock_asyncio_run.call_args
        call_args = args[0].call_args
        self.assertEqual(call_args.kwargs['chat_id'], 'test_log_channel_id')
        self.assertIn("QuizGenerator: Generated quiz for english is not a list", call_args.kwargs['message'])
        self.assertIn(not_a_list_json[:1000], call_args.kwargs['message'])


    @patch('src.generators.Tasks')
    @patch('src.generators.get_random_words')
    @patch('src.generators.asyncio.run')
    def test_generate_quizzes_multiple_languages(self, mock_asyncio_run, mock_get_random_words, MockTasks):
        # Arrange
        languages_to_test = ['english', 'spanish']
        mock_get_random_words.side_effect = lambda lang, count: [MagicMock(word=f"word_{lang}")]
        MockTasks.side_effect = lambda news, language, word: MagicMock(get_prompt=MagicMock(return_value=[{"role": "user", "content": f"Prompt for {language} with {word}"}]))
        english_quizzes_str = '[{"question_id": 1, "lang": "en"}]'
        spanish_quizzes_str = '[{"question_id": 2, "lang": "es"}]'
        self.mock_text_generator.generate_text.side_effect = [english_quizzes_str, spanish_quizzes_str]
        
        quiz_generator = QuizGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier,
            languages=languages_to_test # Use the specific list for this test
        )
        
        # Act
        quizzes_by_lang = quiz_generator.generate_quizzes(news=self.sample_news_list)
        
        # Assert
        self.assertEqual(mock_get_random_words.call_count, 2)
        mock_get_random_words.assert_any_call('english', 1)
        mock_get_random_words.assert_any_call('spanish', 1)

        self.assertEqual(MockTasks.call_count, 2)
        MockTasks.assert_any_call(news=self.sample_news_list, language='english', word='word_english')
        MockTasks.assert_any_call(news=self.sample_news_list, language='spanish', word='word_spanish')

        self.assertEqual(self.mock_text_generator.generate_text.call_count, 2)
        expected_calls_to_ai = [
            call(prompt={"messages": [{"role": "user", "content": "Prompt for english with word_english"}]}),
            call(prompt={"messages": [{"role": "user", "content": "Prompt for spanish with word_spanish"}]})
        ]
        self.mock_text_generator.generate_text.assert_has_calls(expected_calls_to_ai, any_order=False)

        self.assertIn('english', quizzes_by_lang)
        self.assertEqual(quizzes_by_lang['english'], json.loads(english_quizzes_str))
        self.assertIn('spanish', quizzes_by_lang)
        self.assertEqual(quizzes_by_lang['spanish'], json.loads(spanish_quizzes_str))
        
        self.mock_error_notifier.send_message.assert_not_called()
        mock_asyncio_run.assert_not_called()

    @patch('src.generators.Tasks') 
    @patch('src.generators.get_random_words')
    @patch('src.generators.asyncio.run') 
    def test_generate_quizzes_get_random_words_fails(self, mock_asyncio_run, mock_get_random_words, MockTasks):
        # Arrange
        mock_get_random_words.return_value = [] 
        
        quiz_generator = QuizGenerator(
            text_generator=self.mock_text_generator,
            error_notifier=self.mock_error_notifier,
            languages=['english']
        )

        # Act
        quizzes_by_lang = quiz_generator.generate_quizzes(news=self.sample_news_list)

        # Assert
        mock_get_random_words.assert_called_once_with('english', 1)
        MockTasks.assert_not_called() 
        self.mock_text_generator.generate_text.assert_not_called() 
        self.assertIn('english', quizzes_by_lang)
        self.assertEqual(quizzes_by_lang['english'], []) 
        self.mock_error_notifier.send_message.assert_not_called() 
        mock_asyncio_run.assert_not_called()


class TestQuizVerifier(unittest.TestCase):

    def setUp(self):
        self.mock_primary_text_generator = MagicMock(spec=AITextGenerator) # OpenAI-like
        self.mock_verifier_text_generator = MagicMock(spec=AITextGenerator) # Gemini-like
        self.sample_news_articles = [{'id': 1, 'title': 'News 1', 'text': 'Content'}]
        self.sample_questions = {
            'english': [
                {'question_id': 1, 'question': 'Q1 E', 'options': ['a', 'b', 'c', 'd'], 'correct_option_id': 0, 'grammar_topic': 'Topic E1'},
                {'question_id': 2, 'question': 'Q2 E', 'options': ['e', 'f', 'g', 'h'], 'correct_option_id': 1, 'grammar_topic': 'Topic E2'}
            ]
        }
        # This is what Tasks(...).verify(initial_opinion) would return
        self.verification_prompt_from_tasks = [
            {"role": "user", "content": "Verify these questions: Part 1"},
            {"role": "user", "content": "Details: Part 2"}
        ]
        # Expected prompt for verifier (Gemini-like) due to concatenation
        self.expected_verifier_prompt_content = "Verify these questions: Part 1 Details: Part 2"


    @patch('src.generators.Tasks')
    def test_verify_quizzes_all_good(self, MockTasks):
        # Arrange
        MockTasks.return_value.verify.return_value = self.verification_prompt_from_tasks
        
        # Verifier (Gemini) agrees
        self.mock_verifier_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a"]},
            {"question_id": 2, "correct_options": ["f"]}
        ])
        # Primary (OpenAI) agrees
        self.mock_primary_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a"]},
            {"question_id": 2, "correct_options": ["f"]}
        ])
        
        verifier = QuizVerifier(
            primary_text_generator=self.mock_primary_text_generator,
            verifier_text_generator=self.mock_verifier_text_generator,
            languages=['english']
        )

        # Act
        result = verifier.verify_quizzes(
            questions_by_lang=self.sample_questions,
            news_articles=self.sample_news_articles
        )

        # Assert
        MockTasks.return_value.verify.assert_called_once_with(self.sample_questions['english'])
        
        self.mock_verifier_text_generator.generate_text.assert_called_once_with(
            prompt={"messages": [{"role": "user", "content": self.expected_verifier_prompt_content}]}
        )
        self.mock_primary_text_generator.generate_text.assert_called_once_with(
            prompt={"messages": self.verification_prompt_from_tasks}
        )
        
        self.assertEqual(len(result['good']['english']), 2)
        self.assertEqual(result['good']['english'][0]['question_id'], 1)
        self.assertEqual(result['good']['english'][1]['question_id'], 2)
        self.assertEqual(len(result['bad']['english']), 0)

    @patch('src.generators.Tasks')
    def test_verify_quizzes_disagreement(self, MockTasks):
        # Arrange
        MockTasks.return_value.verify.return_value = self.verification_prompt_from_tasks
        
        # Verifier (Gemini) disagrees on Q1
        self.mock_verifier_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["b"]}, # Initial 'a', Verifier 'b'
            {"question_id": 2, "correct_options": ["f"]}
        ])
        # Primary (OpenAI) agrees with initial
        self.mock_primary_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a"]},
            {"question_id": 2, "correct_options": ["f"]}
        ])
        
        verifier = QuizVerifier(
            primary_text_generator=self.mock_primary_text_generator,
            verifier_text_generator=self.mock_verifier_text_generator,
            languages=['english']
        )

        # Act
        result = verifier.verify_quizzes(self.sample_questions, self.sample_news_articles)

        # Assert
        self.assertEqual(len(result['good']['english']), 1)
        self.assertEqual(result['good']['english'][0]['question_id'], 2) # Q2 is good
        self.assertEqual(len(result['bad']['english']), 1)
        self.assertEqual(result['bad']['english'][0]['question_id'], 1) # Q1 is bad
        self.assertIn("Correct option mismatch", result['bad']['english'][0].get('verification_error', ''))


    @patch('src.generators.Tasks')
    def test_verify_quizzes_duplicate_options_in_initial(self, MockTasks):
        # Arrange
        MockTasks.return_value.verify.return_value = self.verification_prompt_from_tasks
        questions_with_duplicates = {
            'english': [
                {'question_id': 1, 'question': 'Q1 Dup', 'options': ['a', 'a', 'b', 'c'], 'correct_option_id': 0},
                self.sample_questions['english'][1] # Q2 is normal
            ]
        }
        # Both AI agree with initial (though Q1 is flawed)
        self.mock_verifier_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a"]},
            {"question_id": 2, "correct_options": ["f"]}
        ])
        self.mock_primary_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a"]},
            {"question_id": 2, "correct_options": ["f"]}
        ])
        
        verifier = QuizVerifier(self.mock_primary_text_generator, self.mock_verifier_text_generator, languages=['english'])

        # Act
        result = verifier.verify_quizzes(questions_with_duplicates, self.sample_news_articles)

        # Assert
        self.assertEqual(len(result['good']['english']), 1) # Q2 should still be good
        self.assertEqual(result['good']['english'][0]['question_id'], 2)
        self.assertEqual(len(result['bad']['english']), 1)
        self.assertEqual(result['bad']['english'][0]['question_id'], 1)
        self.assertEqual(result['bad']['english'][0]['verification_error'], "Duplicate options in initial")


    @patch('src.generators.Tasks')
    def test_verify_quizzes_verifier_json_error(self, MockTasks):
        # Arrange
        MockTasks.return_value.verify.return_value = self.verification_prompt_from_tasks
        self.mock_verifier_text_generator.generate_text.return_value = 'invalid json'
        # Primary agrees with initial
        self.mock_primary_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a"]},
            {"question_id": 2, "correct_options": ["f"]}
        ])
        verifier = QuizVerifier(self.mock_primary_text_generator, self.mock_verifier_text_generator, languages=['english'])

        # Act
        result = verifier.verify_quizzes(self.sample_questions, self.sample_news_articles)

        # Assert
        # Q1 becomes bad because verifier failed, and initial vs primary is the only comparison left.
        # Q2 also becomes bad for the same reason (assuming strict checking if one opinion fails)
        # Current logic: if verifier fails, second_q_match is None.
        # Then it compares initial with third. If they match, it's good.
        self.assertEqual(len(result['good']['english']), 2) # Both should be good as initial and primary match
        self.assertEqual(result['good']['english'][0]['question_id'], 1)
        self.assertEqual(result['good']['english'][1]['question_id'], 2)
        self.assertEqual(len(result['bad']['english']), 0)

    @patch('src.generators.Tasks')
    def test_verify_quizzes_primary_ai_failure(self, MockTasks):
        # Arrange
        MockTasks.return_value.verify.return_value = self.verification_prompt_from_tasks
        self.mock_verifier_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a"]},
            {"question_id": 2, "correct_options": ["f"]}
        ])
        self.mock_primary_text_generator.generate_text.return_value = None # Primary AI fails
        verifier = QuizVerifier(self.mock_primary_text_generator, self.mock_verifier_text_generator, languages=['english'])

        # Act
        result = verifier.verify_quizzes(self.sample_questions, self.sample_news_articles)
        
        # Assert
        # Similar to verifier_json_error, if primary fails, comparison is between initial and verifier.
        self.assertEqual(len(result['good']['english']), 2)
        self.assertEqual(result['good']['english'][0]['question_id'], 1)
        self.assertEqual(result['good']['english'][1]['question_id'], 2)
        self.assertEqual(len(result['bad']['english']), 0)

    @patch('src.generators.Tasks')
    def test_verify_quizzes_multiple_correct_options_from_verifier(self, MockTasks):
        # Arrange
        MockTasks.return_value.verify.return_value = self.verification_prompt_from_tasks
        self.mock_verifier_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a", "b"]}, # Verifier suggests multiple correct
            {"question_id": 2, "correct_options": ["f"]}
        ])
        self.mock_primary_text_generator.generate_text.return_value = json.dumps([
            {"question_id": 1, "correct_options": ["a"]},
            {"question_id": 2, "correct_options": ["f"]}
        ])
        verifier = QuizVerifier(self.mock_primary_text_generator, self.mock_verifier_text_generator, languages=['english'])

        # Act
        result = verifier.verify_quizzes(self.sample_questions, self.sample_news_articles)

        # Assert
        # Q1 is bad because second opinion has != 1 correct options.
        # This check happens in the original code snippet `if len(op2['correct_options']) != 1 ... bad_questions...`
        # However, my current QuizVerifier code doesn't explicitly have that check.
        # It relies on the direct comparison of correct_option_id.
        # Let's re-evaluate the QuizVerifier code. The provided snippet for QuizVerifier does:
        # initial_q_dict.get('correct_option_id') == second_q_match.get('correct_option_id')
        # .get('correct_option_id') on `{"question_id": 1, "correct_options": ["a", "b"]}` would be None.
        # So this comparison would fail.
        # The original code had `op2['correct_options'][0]`. If `correct_options` is `["a", "b"]`, `[0]` is 'a'.
        # My QuizVerifier's logic for comparison is:
        # `initial_q_dict.get('correct_option_id') == second_q_match.get('correct_option_id')`
        # If `second_q_match` is `{"question_id": 1, "correct_options": ["a", "b"]}`, then `second_q_match.get('correct_option_id')` is `None`.
        # So `0 == None` is false. Q1 should be bad.
        self.assertEqual(len(result['good']['english']), 1) # Q2 is good
        self.assertEqual(result['good']['english'][0]['question_id'], 2)
        self.assertEqual(len(result['bad']['english']), 1)
        self.assertEqual(result['bad']['english'][0]['question_id'], 1)
        # The error reason might be "Correct option mismatch" because `None` from `second_q_match.get('correct_option_id')`
        # doesn't match `initial_q_dict.get('correct_option_id')`.
        self.assertIn("Correct option mismatch", result['bad']['english'][0].get('verification_error', ''))


if __name__ == '__main__':
    unittest.main()
