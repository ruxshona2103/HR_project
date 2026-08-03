import json
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.ai_engine.models import InterviewResult
from apps.profile.models import CompanyProfile
from apps.users1.models import User
from apps.vacancies.models import Vacancy

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

        self.assertIn("Junior Python Developer", prompt)
        self.assertIn("REST API", prompt)
        self.assertIn("EMOJILAR", prompt)
        self.assertIn("STRICTLY STANDARD JSON", prompt)
        self.assertIn(self.resume_text, prompt)

    def test_interviewer_prompt_dynamic_level_adaptation(self):
        """Interviewer prompti vakansiya darajasiga (Junior/Senior) moslashishini test qilish."""
        junior_prompt = get_interviewer_prompt(self.junior_vacancy)
        senior_prompt = get_interviewer_prompt(self.senior_vacancy)


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

        mock_response = MagicMock()
        mock_response.choices[0].message.content = fake_ai_message
        mock_client.chat.completions.create.return_value = mock_response


        client_instance = mock_groq_class(api_key="fake_key")
        response = client_instance.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": "Salom"}]
        )

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

        invalid_json_str = "{ 'score': 89, 'feedback': 'Buzilgan string..."

        with self.assertRaises(json.JSONDecodeError):
            json.loads(invalid_json_str)

    def test_early_exit_flag_detection(self):
        """Suhbat oxirida 'SUHBAT YAKUNLANDI' belgisi kelganini aniqlash testi."""

        ai_response_completed = "Rahmat! Suhbatimiz yakunlandi.\nSUHBAT YAKUNLANDI"
        ai_response_ongoing = "Yaxshi, keyingi savol: Redis kesh-xotirasi bilan ishlaganmisiz?"

        is_completed_1 = "SUHBAT YAKUNLANDI" in ai_response_completed
        is_completed_2 = "SUHBAT YAKUNLANDI" in ai_response_ongoing

        self.assertTrue(is_completed_1)
        self.assertFalse(is_completed_2)



"""
KONTEKST
--------
`views.py` ko'rib chiqilganda 2 ta yangi muammo aniqlandi va shu commitda
TUZATILDI (quyidagi testlar tuzatilgan holatni tasdiqlaydi):

    1. CRITICAL (TUZATILDI) — `ResumeCheckAPIView`da `permission_classes`
       UMUMAN yo'q edi. Bu degani, HAR QANDAY anonim tashrifchi cheksiz
       marta AI (Groq) so'rovini yubora olar edi — pullik/tokenlik
       resursni suiiste'mol qilish (abuse/DoS) xavfi. Endi
       `permission_classes = [IsAuthenticated]` qo'shildi.
    2. HIGH (TUZATILDI) — `InterviewStartAPIView`da ham
       `permission_classes` yo'q edi. Endi `IsAuthenticated` qo'shildi.

`InterviewStatusAPIView` va `InterviewFeedbackAPIView`da `permission_classes`
allaqachon to'g'ri edi (`IsAuthenticated`), va `InterviewFeedbackAPIView`da
ownership tekshiruvi (`result.user_id != request.user.id`) ham to'g'ri
ishlagan — bular uchun REGRESSION testlar yozildi, ya'ni kelajakda kimdir
bu qatorlarni bilmasdan o'chirib qo'ysa, testlar darhol qizil bo'lib qoladi.

Real Groq API'ga hech qanday so'rov ketmaydi — `ResumeService.analyze_resume`
har doim mock qilinadi.
"""


def _create_user(email, user_type="candidate"):
    user = User.objects.create(email=email, user_type=user_type)
    user.set_password("StrongPass123!")
    user.save()
    return user


def _create_company_profile(user, **overrides):
    data = dict(name=f"Company of {user.email}")
    data.update(overrides)
    return CompanyProfile.objects.create(user=user, **data)


def _create_vacancy(company, **overrides):
    data = dict(
        title="Backend Developer",
        description="Django/DRF asosida backend ishlab chiquvchi kerak.",
        publish_start="2026-01-01",
        publish_end="2026-02-01",
    )
    data.update(overrides)
    return Vacancy.objects.create(company=company, **data)


def _create_interview_result(user, vacancy_id, **overrides):
    data = dict(
        vacancy_name=str(vacancy_id),
        chat_log=[{"role": "candidate", "content": "Salom"}],
        score=75,
        feedback="Yaxshi natija.",
    )
    data.update(overrides)
    return InterviewResult.objects.create(user=user, **data)


class ResumeCheckPermissionRegressionTests(TestCase):
    """
    CRITICAL (TUZATILDI): anonim foydalanuvchi endi AI resume-tahlil
    so'rovini yubora olmasligi kerak.
    """

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("resume_owner@gmail.com", user_type="organization")
        self.company = _create_company_profile(self.owner)
        self.vacancy = _create_vacancy(self.company)

    def test_anonymous_user_cannot_check_resume(self):
        response = self.client.post(
            reverse("ai-resume-check"),
            {"vacancy_id": self.vacancy.id, "resume_text": "Python tajribam bor"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_fields_returns_400(self):
        candidate = _create_user("resume_candidate@gmail.com")
        self.client.force_authenticate(user=candidate)
        response = self.client.post(reverse("ai-resume-check"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.ai_engine.views.ResumeService.analyze_resume")
    def test_authenticated_user_gets_analysis_result(self, mock_analyze):
        mock_analyze.return_value = json.dumps({"score": 82, "feedback": "Yaxshi mos keladi"})
        candidate = _create_user("resume_candidate2@gmail.com")
        self.client.force_authenticate(user=candidate)

        response = self.client.post(
            reverse("ai-resume-check"),
            {"vacancy_id": self.vacancy.id, "resume_text": "Python/Django tajribam bor"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["score"], 82)
        mock_analyze.assert_called_once()

    @patch("apps.ai_engine.views.ResumeService.analyze_resume")
    def test_nonexistent_vacancy_returns_404(self, mock_analyze):
        mock_analyze.side_effect = Vacancy.DoesNotExist
        candidate = _create_user("resume_candidate3@gmail.com")
        self.client.force_authenticate(user=candidate)

        response = self.client.post(
            reverse("ai-resume-check"),
            {"vacancy_id": 999999, "resume_text": "Matn"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("apps.ai_engine.views.ResumeService.analyze_resume")
    def test_service_exception_returns_500_not_a_crash(self, mock_analyze):
        """AI xizmati kutilmagan xato bersa ham, view 500 tuzilgan javob bilan yopilishi kerak."""
        mock_analyze.side_effect = RuntimeError("Groq API vaqtincha ishlamayapti")
        candidate = _create_user("resume_candidate4@gmail.com")
        self.client.force_authenticate(user=candidate)

        response = self.client.post(
            reverse("ai-resume-check"),
            {"vacancy_id": self.vacancy.id, "resume_text": "Matn"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)


class InterviewStartPermissionRegressionTests(TestCase):
    """HIGH (TUZATILDI): anonim foydalanuvchi endi intervyu boshlash ma'lumotini ololmaydi."""

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("start_owner@gmail.com", user_type="organization")
        self.company = _create_company_profile(self.owner)
        self.vacancy = _create_vacancy(self.company)

    def test_anonymous_user_cannot_start_interview(self):
        url = reverse("ai-interview-start", kwargs={"vacancy_id": self.vacancy.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_gets_ws_url(self):
        candidate = _create_user("start_candidate@gmail.com")
        self.client.force_authenticate(user=candidate)
        url = reverse("ai-interview-start", kwargs={"vacancy_id": self.vacancy.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["vacancy_title"], self.vacancy.title)
        self.assertIn(f"/ws/interview/{self.vacancy.id}/", response.data["ws_url"])

    def test_nonexistent_vacancy_returns_404(self):
        candidate = _create_user("start_candidate2@gmail.com")
        self.client.force_authenticate(user=candidate)
        url = reverse("ai-interview-start", kwargs={"vacancy_id": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InterviewStatusRegressionTests(TestCase):
    """`permission_classes` avvaldan to'g'ri edi — bu yerdagi testlar regressiyani ushlab qoladi."""

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("status_owner@gmail.com", user_type="organization")
        self.company = _create_company_profile(self.owner)
        self.vacancy = _create_vacancy(self.company)

    def test_anonymous_user_cannot_check_status(self):
        url = reverse("ai-interview-status", kwargs={"vacancy_id": self.vacancy.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_not_started_when_no_result_exists(self):
        candidate = _create_user("status_candidate@gmail.com")
        self.client.force_authenticate(user=candidate)
        url = reverse("ai-interview-status", kwargs={"vacancy_id": self.vacancy.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "not_started")

    def test_returns_completed_with_score_when_result_exists(self):
        candidate = _create_user("status_candidate2@gmail.com")
        _create_interview_result(candidate, self.vacancy.id, score=90)
        self.client.force_authenticate(user=candidate)

        url = reverse("ai-interview-status", kwargs={"vacancy_id": self.vacancy.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
        self.assertEqual(response.data["score"], 90)

    def test_does_not_leak_other_users_result(self):
        """Boshqa userning shu vakansiya bo'yicha natijasi bu userga 'completed' sifatida ko'rinmasligi kerak."""
        other = _create_user("status_other@gmail.com")
        _create_interview_result(other, self.vacancy.id, score=99)

        candidate = _create_user("status_candidate3@gmail.com")
        self.client.force_authenticate(user=candidate)

        url = reverse("ai-interview-status", kwargs={"vacancy_id": self.vacancy.id})
        response = self.client.get(url)
        self.assertEqual(response.data["status"], "not_started")


class InterviewFeedbackIDORRegressionTests(TestCase):
    """
    `InterviewFeedbackAPIView`da ownership tekshiruvi avvaldan to'g'ri
    ishlagan (`result.user_id != request.user.id` -> 403). Bu testlar
    o'sha himoyani regression sifatida qulflab qo'yadi.
    """

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("fb_owner@gmail.com", user_type="organization")
        self.company = _create_company_profile(self.owner)
        self.vacancy = _create_vacancy(self.company)
        self.candidate = _create_user("fb_candidate@gmail.com")
        self.attacker = _create_user("fb_attacker@gmail.com")
        self.result = _create_interview_result(
            self.candidate, self.vacancy.id, score=88, feedback="Zo'r natija!"
        )

    def test_anonymous_user_cannot_view_feedback(self):
        url = reverse("ai-interview-feedback", kwargs={"result_id": self.result.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_view_own_feedback(self):
        self.client.force_authenticate(user=self.candidate)
        url = reverse("ai-interview-feedback", kwargs={"result_id": self.result.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["score"], 88)

    def test_other_user_cannot_view_someone_elses_feedback(self):
        """IDOR regression: boshqa userning natijasini ko'rishga urinish 403 bilan yopilishi kerak."""
        self.client.force_authenticate(user=self.attacker)
        url = reverse("ai-interview-feedback", kwargs={"result_id": self.result.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_result_returns_404(self):
        self.client.force_authenticate(user=self.candidate)
        url = reverse("ai-interview-feedback", kwargs={"result_id": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)