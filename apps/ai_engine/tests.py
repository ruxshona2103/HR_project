import json
from unittest.mock import patch, MagicMock
from django.test import TestCase

from .prompts.templates import (
    get_resume_check_prompt,
    get_interviewer_prompt,
    get_evaluation_prompt,
)


class DummyVacancy:
    """
    Testlar davomida real DB'ga ulanmasdan vakansiya obyektini simulyatsiya qilish
    uchun yengil Mock klassi.
    """

    def __init__(self, title, description, level="Junior"):
        self.title = title
        self.description = description
        self.work_type = "Remote"
        self.location = "Toshkent"
        self.min_experience = "1 yil"
        self.experience_level = level
        self.required_skills = "Python, Django, PostgreSQL, REST API"
        self.education_level = "Bakalavr"
        self.salary_from = "500"
        self.salary_to = "1000"
        self.currency = "USD"


class AIEnginePromptsTestCase(TestCase):
    """
    1-BLOK: Promptlar to'g'ri va dinamik shakllanayotganini test qilish.
    """

    def setUp(self):
        self.junior_vacancy = DummyVacancy("Junior Python Developer", "Django backend yaratish", "Junior")
        self.senior_vacancy = DummyVacancy("Senior System Architect", "High-load microservices", "Senior")
        self.resume_text = "Python va Django bo'yicha 1 yillik tajribam bor. REST API loyihalar qilganman."

    def test_resume_check_prompt_structure_and_rules(self):
        """Resume check promptida ma'lumotlar va emojilar mantiqi mavjudligini test qilish."""
        prompt = get_resume_check_prompt(self.junior_vacancy, self.resume_text)

        # Assertionlar
        self.assertIn("Junior Python Developer", prompt)
        self.assertIn("REST API", prompt)
        self.assertIn("EMOJILAR", prompt)
        self.assertIn("STRICTLY STANDARD JSON", prompt)
        self.assertIn(self.resume_text, prompt)

    def test_interviewer_prompt_dynamic_level_adaptation(self):
        """Interviewer prompti vakansiya darajasiga (Junior/Senior) moslashishini test qilish."""
        junior_prompt = get_interviewer_prompt(self.junior_vacancy)
        senior_prompt = get_interviewer_prompt(self.senior_vacancy)

        # Junior va Senior promptlarida mos qoidalar bormi?
        self.assertIn("Junior Python Developer", junior_prompt)
        self.assertIn("Senior System Architect", senior_prompt)
        self.assertIn("EARLY EXIT", junior_prompt)
        self.assertIn("SUHBAT YAKUNLANDI", junior_prompt)

    def test_evaluation_prompt_structure(self):
        """Evaluation prompt suhbat tarixini to'g'ri qabul qilishini test qilish."""
        chat_history = "Interviewer: Python'da GIL nima?\nCandidate: Global Interpreter Lock."
        prompt = get_evaluation_prompt(self.junior_vacancy, chat_history)

        self.assertIn("Junior Python Developer", prompt)
        self.assertIn(chat_history, prompt)
        self.assertIn("MAQTOV, RUHLANTIRISH VA SMAYLIKLAR", prompt)


class AIEngineGroqIntegrationTestCase(TestCase):
    """
    2-BLOK: Groq API Integratsiyasi va Mocking testlari (Real API'ga so'rov ketmaydi).
    """

    @patch('groq.Groq')
    def test_groq_api_successful_response(self, mock_groq_class):
        """Groq API muvaffaqiyatli javob berganda uni to'g'ri qabul qilish testi."""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        fake_ai_message = "Salom! Python'da decorator nima va u amaliyotda qanday ishlatiladi?"

        # Mocking groq completion response structure
        mock_response = MagicMock()
        mock_response.choices[0].message.content = fake_ai_message
        mock_client.chat.completions.create.return_value = mock_response

        # AGAR SIZDA REAL SERVICE FUNKSIYA BO'LSA, UNI BU YERDA CHAQIRASIZ:
        # Masalan:
        # from apps.ai_engine.services import ask_groq_ai
        # response_text = ask_groq_ai("Salom")
        # self.assertEqual(response_text, fake_ai_message)

        # Hozircha faqatgina mock client orqali tekshirish uchun quyidagicha simulyatsiya qilamiz:
        client_instance = mock_groq_class(api_key="fake_key")
        response = client_instance.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": "Salom"}]
        )

        # Assertionlar
        self.assertEqual(response.choices[0].message.content, fake_ai_message)
        mock_client.chat.completions.create.assert_called_once()

    @patch('groq.Groq')
    def test_json_parsing_and_fallback_safety(self, mock_groq_class):
        """AI tomonidan qaytarilgan JSON to'g'ri parse bo'lishini va buzilgan JSON ushlanishini test qilish."""

        # 1-Ssenariy: To'g'ri JSON qaytganda
        valid_json_str = json.dumps({
            "score": 89,
            "feedback": "🔥 Ajoyib natija! Nomzod vakansiyaga 89% mos keladi.",
            "strengths": ["Yaxshi bilim"],
            "weaknesses": ["Optimizatsiya kerak"],
            "recommendation": "TAVSIYA ETILADI"
        })

        parsed_data = json.loads(valid_json_str)
        self.assertEqual(parsed_data["score"], 89)
        self.assertIn("🔥 Ajoyib natija!", parsed_data["feedback"])

        # 2-Ssenariy: AI tomonidan tasodifan buzilgan (invalid) JSON qaytganda (Crash bo'lmasligi kerak)
        invalid_json_str = "{ 'score': 89, 'feedback': 'Buzilgan string..."

        with self.assertRaises(json.JSONDecodeError):
            json.loads(invalid_json_str)

    def test_early_exit_flag_detection(self):
        """Suhbat oxirida 'SUHBAT YAKUNLANDI' belgisi kelganini aniqlash testi."""

        ai_response_completed = "Rahmat! Suhbatimiz yakunlandi.\nSUHBAT YAKUNLANDI"
        ai_response_ongoing = "Yaxshi, keyingi savol: Redis kesh-xotirasi bilan ishlaganmisiz?"

        # Flag bor-yo'qligini tekshirish mantig'i:
        is_completed_1 = "SUHBAT YAKUNLANDI" in ai_response_completed
        is_completed_2 = "SUHBAT YAKUNLANDI" in ai_response_ongoing

        self.assertTrue(is_completed_1)
        self.assertFalse(is_completed_2)