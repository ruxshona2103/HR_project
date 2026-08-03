from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profile.models import CompanyProfile
from apps.users1.models import User
from apps.vacancies.models import Candidate, Vacancy


def vacancy_payload(**overrides):
    """Vakansiya yaratish/yangilash uchun to'liq va valid payload."""
    today = date.today()
    data = {
        "title": "Backend dasturchi",
        "description": "Django/DRF asosida backend dasturchi kerak.",
        "required_skills": "Python, Django, PostgreSQL",
        "min_experience": 3,
        "publish_start": today.isoformat(),
        "publish_end": (today + timedelta(days=30)).isoformat(),
        "daily_hours": "8",
    }
    data.update(overrides)
    return data


class VacancyTestSetupMixin:
    """Umumiy foydalanuvchi/kompaniya obyektlarini yaratadi."""

    def setUp(self):
        self.org_user = User.objects.create_user(
            email="org1@example.com", password="pass12345", user_type="organization"
        )
        self.company = CompanyProfile.objects.create(user=self.org_user, name="Company One")

        self.other_org_user = User.objects.create_user(
            email="org2@example.com", password="pass12345", user_type="organization"
        )
        self.other_company = CompanyProfile.objects.create(user=self.other_org_user, name="Company Two")

        self.org_user_without_company = User.objects.create_user(
            email="org3@example.com", password="pass12345", user_type="organization"
        )

        self.candidate_user = User.objects.create_user(
            email="candidate@example.com", password="pass12345", user_type="candidate"
        )

        self.vacancy = Vacancy.objects.create(
            company=self.company,
            title="Python dasturchi",
            description="Test vakansiya",
            required_skills="Python, Django, PostgreSQL",
            min_experience=3,
            publish_start=date.today(),
            publish_end=date.today() + timedelta(days=30),
        )

        self.list_url = reverse("vacancy-list")
        self.detail_url = reverse("vacancy-detail", args=[self.vacancy.id])


class VacancyPermissionTests(VacancyTestSetupMixin, APITestCase):

    def test_anonymous_can_list_vacancies(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_can_retrieve_vacancy(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.vacancy.title)


    def test_anonymous_cannot_create_vacancy(self):
        response = self.client.post(self.list_url, vacancy_payload(), format="json")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_candidate_cannot_create_vacancy(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.post(self.list_url, vacancy_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_organization_without_company_profile_cannot_create(self):
        self.client.force_authenticate(self.org_user_without_company)
        response = self.client.post(self.list_url, vacancy_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company", response.data)

    def test_organization_with_company_creates_vacancy(self):
        self.client.force_authenticate(self.org_user)
        response = self.client.post(self.list_url, vacancy_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Vacancy.objects.get(id=response.data["id"])
        self.assertEqual(created.company, self.company)

    def test_company_field_cannot_be_spoofed_on_create(self):
        """Client boshqa kompaniya id'sini yuborsa ham, u e'tiborga olinmasligi kerak."""
        self.client.force_authenticate(self.org_user)
        response = self.client.post(
            self.list_url, vacancy_payload(company=self.other_company.id), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Vacancy.objects.get(id=response.data["id"])
        self.assertEqual(created.company, self.company)


    def test_owner_can_update_own_vacancy(self):
        self.client.force_authenticate(self.org_user)
        response = self.client.patch(self.detail_url, {"title": "Yangilangan sarlavha"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vacancy.refresh_from_db()
        self.assertEqual(self.vacancy.title, "Yangilangan sarlavha")

    def test_non_owner_cannot_update_vacancy(self):
        self.client.force_authenticate(self.other_org_user)
        response = self.client.patch(self.detail_url, {"title": "Boshqa sarlavha"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.vacancy.refresh_from_db()
        self.assertNotEqual(self.vacancy.title, "Boshqa sarlavha")

    def test_owner_can_delete_own_vacancy(self):
        self.client.force_authenticate(self.org_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vacancy.objects.filter(id=self.vacancy.id).exists())

    def test_non_owner_cannot_delete_vacancy(self):
        self.client.force_authenticate(self.other_org_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Vacancy.objects.filter(id=self.vacancy.id).exists())

    def test_anonymous_cannot_update_or_delete(self):
        response = self.client.patch(self.detail_url, {"title": "X"}, format="json")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        response = self.client.delete(self.detail_url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class VacancySerializerValidationTests(VacancyTestSetupMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.org_user)

    def test_salary_requires_currency(self):
        payload = vacancy_payload(salary_from="1000", salary_to="2000")
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("currency", response.data)

    def test_salary_to_cannot_be_less_than_salary_from(self):
        payload = vacancy_payload(salary_from="2000", salary_to="1000", currency="USD")
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("salary_to", response.data)

    def test_valid_salary_range_is_accepted(self):
        payload = vacancy_payload(salary_from="1000", salary_to="2000", currency="USD")
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_publish_end_cannot_be_before_publish_start(self):
        today = date.today()
        payload = vacancy_payload(
            publish_start=today.isoformat(),
            publish_end=(today - timedelta(days=1)).isoformat(),
        )
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("publish_end", response.data)


class VacancyMatchScoreTests(VacancyTestSetupMixin, APITestCase):
    """
    Vacancy.min_experience=3, required_skills="Python, Django, PostgreSQL"
    (setUp'dagi self.vacancy asosida).
    """

    def test_no_candidate_id_returns_none(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["match_score"])

    def test_unknown_candidate_id_returns_none(self):
        response = self.client.get(self.detail_url, {"candidate_id": 999999})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["match_score"])

    def test_full_skill_and_experience_match_scores_100(self):
        candidate = Candidate.objects.create(
            name="To'liq mos nomzod", skills="Python, Django, PostgreSQL", experience=5
        )
        response = self.client.get(self.detail_url, {"candidate_id": candidate.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["match_score"], 100)

    def test_partial_skill_match_and_insufficient_experience(self):
        candidate = Candidate.objects.create(
            name="Qisman mos nomzod", skills="Python, Go", experience=1
        )
        response = self.client.get(self.detail_url, {"candidate_id": candidate.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        skill_score = (1 / 3) * 50
        experience_score = (1 / 3) * 50
        expected = int(skill_score + experience_score)
        self.assertEqual(response.data["match_score"], expected)

    def test_no_matching_skills_scores_experience_only(self):
        candidate = Candidate.objects.create(
            name="Ko'nikmasi mos emas", skills="Go, Rust", experience=5
        )
        response = self.client.get(self.detail_url, {"candidate_id": candidate.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["match_score"], 50)
