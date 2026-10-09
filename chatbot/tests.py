"""
Regression tests for Chatbot conversational flow, shortcut actions, and context retention.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from unittest.mock import patch
import json

User = get_user_model()


class ChatbotFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='chattestuser',
            email='chattest@placementpro.com',
            password='testpassword123'
        )
        self.client = Client()
        self.client.login(username='chattestuser', password='testpassword123')

    def test_chatbot_page_renders_with_placement_assistant_welcome(self):
        """Verify chatbot interface renders the AI Placement Assistant welcome message and shortcuts."""
        response = self.client.get('/chatbot/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Placement Assistant")
        self.assertContains(response, "Study Plans &amp; Schedules")
        self.assertContains(response, "Resume Review &amp; ATS Score")
        self.assertContains(response, "Interview Tips")
        self.assertContains(response, "Companies")
        self.assertContains(response, "Aptitude")

    @patch('core.ai_service._generate')
    def test_valid_ai_response_returned_instead_of_welcome_message(self, mock_generate):
        """Verify dynamic AI response is returned and not the generic welcome greeting."""
        mock_generate.return_value = "Binary search works by repeatedly dividing the search interval in half."

        resp = self.client.post(
            '/chatbot/ask/',
            data=json.dumps({'message': 'Explain binary search in simple words.', 'mode': 'tutor'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertIn("Binary search works", data.get('response'))
        self.assertNotIn("I'm your AI Placement Assistant! I can help you with", data.get('response'))

    @patch('core.ai_service._generate')
    def test_multi_turn_follow_up_preserves_context(self, mock_generate):
        """Verify follow-up message receives an appropriate response and passes history."""
        # Turn 1
        mock_generate.return_value = "Here are five aptitude questions: 1. Ratio... 2. Profit..."
        self.client.post(
            '/chatbot/ask/',
            data=json.dumps({'message': 'Give me five aptitude questions with answers.', 'mode': 'tutor'}),
            content_type='application/json'
        )

        # Turn 2: Follow up
        mock_generate.return_value = "In your previous message, you asked for five aptitude questions."
        resp = self.client.post(
            '/chatbot/ask/',
            data=json.dumps({'message': 'What did I ask you to do in my previous message?', 'mode': 'tutor'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertIn("aptitude questions", data.get('response'))

        # Check session history contains both turns
        session = self.client.session
        history = session.get('chat_history', [])
        self.assertEqual(len(history), 4)  # 2 user msgs, 2 assistant msgs
        self.assertEqual(history[0]['content'], 'Give me five aptitude questions with answers.')
        self.assertEqual(history[2]['content'], 'What did I ask you to do in my previous message?')

    @patch('core.ai_service._generate')
    def test_provider_error_does_not_become_fake_welcome_response(self, mock_generate):
        """Verify API provider failure returns an honest error status and message."""
        mock_generate.return_value = None  # Simulates provider failure

        resp = self.client.post(
            '/chatbot/ask/',
            data=json.dumps({'message': 'Create a study plan', 'mode': 'tutor'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get('success'))
        self.assertIn("temporarily unavailable", data.get('response').lower())
        self.assertNotIn("I'm your AI Placement Assistant! I can help you with", data.get('response'))

    @patch('core.ai_service._generate')
    def test_shortcut_prompts_produce_specialized_answers(self, mock_generate):
        """Verify shortcut buttons trigger specialized requests and answers."""
        shortcuts = {
            'study_plans': 'Give me a 7-day placement preparation plan and study schedule.',
            'resume_review': 'How do I review my resume to achieve a high ATS score? What are the key sections and keywords?',
            'interview_tips': 'Give me essential interview preparation tips for technical and HR rounds, including the STAR method.',
            'companies': 'What are the typical interview rounds, eligibility criteria, and preparation strategies for top product and service companies?',
            'aptitude': 'Give me five aptitude questions with answers and step-by-step explanations.',
        }

        for sc, prompt in shortcuts.items():
            mock_generate.return_value = f"Specialized response for {sc}"
            resp = self.client.post(
                '/chatbot/ask/',
                data=json.dumps({'message': prompt, 'mode': 'tutor'}),
                content_type='application/json'
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get('success'))
            self.assertEqual(data.get('response'), f"Specialized response for {sc}")

    def test_clear_chat_empties_session_history(self):
        """Verify clearing chat removes conversation history."""
        session = self.client.session
        session['chat_history'] = [{'role': 'user', 'content': 'Hello'}]
        session.save()

        resp = self.client.post('/chatbot/clear/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.client.session.get('chat_history'), [])
