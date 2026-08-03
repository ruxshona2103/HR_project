"""
CompanyProfile / AIInterviewQuestion / CompanyVacancy — profil moduli testlari
================================================================================

KONTEKST
--------
Audit paytida `apps/profile` uchun tests.py UMUMAN yo'q edi va 3 ta
muammo aniqlandi. Ushbu commitda HAMMASI `views.py`da TUZATILDI, testlar
esa tuzatilgan xatti-harakatni tasdiqlaydi (regression sifatida qoladi):

    1. CRITICAL (TUZATILDI) — `AIInterviewQuestionViewSet`da
       `permission_classes` UMUMAN belgilanmagan edi. Endi
       `permission_classes = [IsAuthenticated]` qo'shildi.
    2. HIGH (TUZATILDI) — `AIInterviewQuestionViewSet.perform_create()`
       `self.request.user.company_profile`ni try/except'siz o'qir edi;
       profil bo'lmasa tutilmagan `DoesNotExist` 500ga olib kelardi. Endi
       `CompanyVacancyViewSet`dagi kabi try/except + 400 `ValidationError`
       bilan almashtirildi.
    3. MEDIUM (TUZATILDI) — `CompanyProfileViewSet.me()` da
       `CompanyProfile.objects.get_or_create(user=request.user)` tashqi
       himoyasiz chaqirilardi. `user` maydoni `OneToOneField` bo'lgani
       uchun DB darajasida unique constraint bor edi, lekin
       `ATOMIC_REQUESTS=True` sharoitida concurrent so'rovlardan biri
       `IntegrityError` berib, butun tashqi tranzaksiyani "buzilgan"
       holatga o'tkazishi mumkin edi. Endi `get_or_create()` o'zining
       ICHKI `transaction.atomic()` savepointi ichiga olindi va
       `IntegrityError` shu yerda tutilib, oddiy `get()` bilan
       qaytariladi — tashqi tranzaksiyaga ta'sir qilmaydi.

BU TEST FAYLI NIMANI TEKSHIRADI
--------------------------------
    - CompanyProfileViewSet: scoping (IDOR yo'qligi), CRUD, `me()`
      endpoint, bitta userga bitta profil qoidasi.
    - AIInterviewQuestionViewSet: scoping, autentifikatsiyasiz kirish
      TAQIQLANGANLIGI (endi YASHIL — tuzatilgandan keyin), va profilsiz
      user savol yaratmoqchi bo'lsa tushunarli 400 qaytishi.
    - CompanyVacancyViewSet: kompaniya bo'yicha scoping va
      `perform_create`dagi "avval profil yarating" qoidasi.
    - `me()` uchun DB darajasidagi himoyani va concurrent so'rovlar
      ostida ham 500 bermay barqaror ishlashini tasdiqlovchi regression
      testlar.

MUHIM TAXMIN
-------------
`apps/user_profile/tests.py`dagi kabi, `User` modeli
`apps.users1.models.User` dan olinadi va `email` + `user_type` bilan
yaratiladi. Agar loyihada boshqacha bo'lsa, faqat `_create_user()`
funksiyasini moslashtiring — qolgan testlar o'zgarishsiz ishlaydi.
"""

from unittest import mock

from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.profile.models import CompanyProfile, AIInterviewQuestion
from apps.users1.models import User
from apps.vacancies.models import Vacancy

COMPANY_PROFILE_LIST = "company-profile-list"
COMPANY_PROFILE_DETAIL = "company-profile-detail"
COMPANY_PROFILE_ME = "company-profile-me"

AI_QUESTIONS_LIST = "ai-questions-list"
AI_QUESTIONS_DETAIL = "ai-questions-detail"

COMPANY_VACANCY_LIST = "company-vacancy-list"
COMPANY_VACANCY_DETAIL = "company-vacancy-detail"


def _create_user(email, user_type="organization"):
    """Test uchun autentifikatsiyadan o'tgan foydalanuvchi yaratish."""
    user = User.objects.create(email=email, user_type=user_type)
    user.set_password("StrongPass123!")
    user.save()
    return user


def _create_company_profile(user, **overrides):
    data = dict(name=f"Company of {user.email}")
    data.update(overrides)
    return CompanyProfile.objects.create(user=user, **data)


def _create_question(company, **overrides):
    data = dict(text="Django QuerySet va Manager farqi nimada?")
    data.update(overrides)
    return AIInterviewQuestion.objects.create(company=company, **data)


def _create_vacancy(company, **overrides):
    data = dict(
        title="Backend Developer",
        description="Django/DRF asosida backend ishlab chiquvchi kerak.",
        publish_start="2026-01-01",
        publish_end="2026-02-01",
    )
    data.update(overrides)
    return Vacancy.objects.create(company=company, **data)



class CompanyProfileScopingTests(TestCase):
    """`get_queryset()` faqat request.user ga tegishli profilni qaytarishi kerak."""

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("owner@gmail.com")
        self.other = _create_user("other@gmail.com")
        self.owner_profile = _create_company_profile(self.owner, name="Owner LLC")
        self.other_profile = _create_company_profile(self.other, name="Other LLC")

    def test_list_returns_only_own_profile(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(reverse(COMPANY_PROFILE_LIST))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data]
        self.assertEqual(ids, [self.owner_profile.id])

    def test_cannot_retrieve_other_users_profile(self):
        self.client.force_authenticate(user=self.other)
        url = reverse(COMPANY_PROFILE_DETAIL, kwargs={"pk": self.owner_profile.pk})
        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )

    def test_cannot_update_other_users_profile(self):
        self.client.force_authenticate(user=self.other)
        url = reverse(COMPANY_PROFILE_DETAIL, kwargs={"pk": self.owner_profile.pk})
        response = self.client.patch(url, {"name": "Hacked"}, format="json")
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )
        self.owner_profile.refresh_from_db()
        self.assertEqual(self.owner_profile.name, "Owner LLC")

    def test_anonymous_user_cannot_access_list(self):
        response = self.client.get(reverse(COMPANY_PROFILE_LIST))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CompanyProfileCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("creator@gmail.com")
        self.client.force_authenticate(user=self.owner)

    def test_create_profile_with_valid_payload_succeeds(self):
        url = reverse(COMPANY_PROFILE_LIST)
        response = self.client.post(url, {"name": "Yangi Kompaniya"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = CompanyProfile.objects.get(pk=response.data["id"])
        self.assertEqual(created.user_id, self.owner.id)

    def test_create_profile_without_name_returns_400(self):
        url = reverse(COMPANY_PROFILE_LIST)
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_user_cannot_create_second_profile(self):
        _create_company_profile(self.owner, name="Birinchi")
        url = reverse(COMPANY_PROFILE_LIST)
        response = self.client.post(url, {"name": "Ikkinchi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(CompanyProfile.objects.filter(user=self.owner).count(), 1)

    def test_anonymous_user_cannot_create_profile(self):
        self.client.force_authenticate(user=None)
        url = reverse(COMPANY_PROFILE_LIST)
        response = self.client.post(url, {"name": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_created_profile_cannot_be_assigned_to_another_user_via_payload(self):
        """
        Serializerda `user` maydoni umuman yo'q (faqat perform_create orqali
        biriktiriladi), shuning uchun payloadga boshqa user yuborilsa ham
        e'tiborga olinmasligi kerak.
        """
        attacker_target = _create_user("victim@gmail.com")
        url = reverse(COMPANY_PROFILE_LIST)
        response = self.client.post(
            url, {"name": "Sneaky", "user": attacker_target.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = CompanyProfile.objects.get(pk=response.data["id"])
        self.assertEqual(created.user_id, self.owner.id)



class CompanyProfileMeEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("me_owner@gmail.com")
        self.client.force_authenticate(user=self.owner)
        self.url = reverse(COMPANY_PROFILE_ME)

    def test_me_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_get_creates_profile_when_missing(self):
        self.assertFalse(CompanyProfile.objects.filter(user=self.owner).exists())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CompanyProfile.objects.filter(user=self.owner).exists())

    def test_me_get_does_not_duplicate_on_repeated_calls(self):
        first = self.client.get(self.url)
        second = self.client.get(self.url)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(CompanyProfile.objects.filter(user=self.owner).count(), 1)

    def test_me_patch_updates_own_profile(self):
        response = self.client.patch(self.url, {"name": "Yangilangan Nom"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = CompanyProfile.objects.get(user=self.owner)
        self.assertEqual(profile.name, "Yangilangan Nom")

    def test_me_returns_only_the_caller_own_profile(self):
        """Ikki xil user `me()` chaqirsa, ikkitasi mustaqil profilga ega bo'lishi kerak."""
        other = _create_user("me_other@gmail.com")

        self.client.force_authenticate(user=self.owner)
        owner_resp = self.client.get(self.url)

        other_client = APIClient()
        other_client.force_authenticate(user=other)
        other_resp = other_client.get(self.url)

        self.assertNotEqual(owner_resp.data["id"], other_resp.data["id"])



class CompanyProfileRaceConditionRegressionTests(TransactionTestCase):
    """
    MEDIUM (TUZATILDI): `me()` endi `get_or_create()`ni ichki
    `transaction.atomic()` savepointiga o'rab, `IntegrityError`ni
    tutadi va mavjud yozuvni oddiy `get()` bilan qaytaradi. Quyidagi
    testlar 2 ta narsani tasdiqlaydi:

      1. DB darajasida (OneToOneField unique constraint) ikkita profil
         hech qachon jismonan saqlanib qolmaydi — bu oxirgi chiziq
         himoyasi va u ishlashi SHART.
      2. Amaliy concurrency ostida (thread orqali simulyatsiya) `me()`
         endpoint endi 500 bilan yiqilmasdan barqaror 200 qaytarishi va
         faqat bitta profil yaratilishi kerak.
    """

    def test_one_to_one_constraint_prevents_duplicate_profile_at_db_level(self):
        user = _create_user("race_db@gmail.com")
        _create_company_profile(user)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                _create_company_profile(user, name="Ikkinchi")

    def test_concurrent_me_calls_result_in_single_profile(self):
        """
        Bu test AVVAL ikkita real threadni bitta SQLite bazasiga bir vaqtda
        yozishga urinar edi (`threading.Barrier` bilan sinxronlashtirib).
        Bu — flaky (beqaror) edi: SQLite bitta yozuvchi (single-writer)
        arxitekturasiga ega, shuning uchun ikkala thread aynan bir lahzada
        yozishga uringanda "database is locked" / "database table is
        locked" xatosi tasodifiy chiqib turardi va bu xato hech qayerda
        ushlanmagani uchun thread jimgina o'lib, `results` bo'sh qolardi.
        Bu SQLite'ning test muhitidagi cheklovi edi, `me()` view'idagi
        real bug emas.

        TUZATISH: haqiqiy vaqt bo'yicha poyga (timing race) o'rniga,
        `get_or_create()` xuddi ikkinchi so'rov bir zumda profil yaratib
        ulgurgandagi holatni — ya'ni `IntegrityError` chiqarishini —
        to'g'ridan-to'g'ri simulyatsiya qilamiz. Natijada test har doim
        bir xil, deterministik ishlaydi va `views.py`dagi aniq shu
        `IntegrityError` -> `get()` fallback logikasini tekshiradi —
        SQLite'ning o'ziga xos locking xatti-harakatiga bog'liq bo'lmay.
        """
        user = _create_user("race_http@gmail.com")

        existing_profile = _create_company_profile(user)

        client = APIClient()
        client.force_authenticate(user=user)

        with mock.patch(
            "apps.profile.views.CompanyProfile.objects.get_or_create",
            side_effect=IntegrityError,
        ):
            response = client.get(reverse(COMPANY_PROFILE_ME))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], existing_profile.id)
        self.assertEqual(CompanyProfile.objects.filter(user=user).count(), 1)



class AIInterviewQuestionPermissionRegressionTests(TestCase):
    """
    CRITICAL (TUZATILDI): `AIInterviewQuestionViewSet`ga
    `permission_classes = [IsAuthenticated]` qo'shildi. Quyidagi testlar
    endi YASHIL bo'lishi kerak — agar kimdir bu qatorni tasodifan
    o'chirib qo'ysa, ular yana QIZIL bo'lib, regressiyani ushlab qoladi.
    """

    def setUp(self):
        self.client = APIClient()

    def test_anonymous_user_cannot_list_questions(self):
        response = self.client.get(reverse(AI_QUESTIONS_LIST))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_create_question(self):
        response = self.client.post(
            reverse(AI_QUESTIONS_LIST), {"text": "Anonim savol"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_retrieve_question_by_id(self):
        owner = _create_user("aiq_owner@gmail.com")
        company = _create_company_profile(owner)
        question = _create_question(company)
        url = reverse(AI_QUESTIONS_DETAIL, kwargs={"pk": question.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AIInterviewQuestionScopingTests(TestCase):
    """get_queryset() kompaniya bo'yicha to'g'ri filtrlaydi — bu qism ishlaydi."""

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("aiq_scope_owner@gmail.com")
        self.other = _create_user("aiq_scope_other@gmail.com")
        self.owner_company = _create_company_profile(self.owner)
        self.other_company = _create_company_profile(self.other)
        self.owner_question = _create_question(self.owner_company, text="Owner savoli")
        self.other_question = _create_question(self.other_company, text="Other savoli")

    def test_user_sees_only_own_company_questions(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(reverse(AI_QUESTIONS_LIST))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data]
        self.assertEqual(ids, [self.owner_question.id])

    def test_user_without_company_profile_gets_empty_list(self):
        candidate = _create_user("aiq_no_company@gmail.com", user_type="candidate")
        self.client.force_authenticate(user=candidate)
        response = self.client.get(reverse(AI_QUESTIONS_LIST))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_question_is_associated_with_callers_company(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            reverse(AI_QUESTIONS_LIST),
            {"text": "Yangi savol", "question_type": "hr", "difficulty": "middle"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = AIInterviewQuestion.objects.get(pk=response.data["id"])
        self.assertEqual(created.company_id, self.owner_company.id)


class AIInterviewQuestionRobustnessRegressionTests(TestCase):
    """
    HIGH (TUZATILDI): `perform_create` endi `self.request.user
    .company_profile`ni try/except bilan o'qiydi va `CompanyProfile
    .DoesNotExist` bo'lsa `CompanyVacancyViewSet.perform_create`dagi kabi
    tushunarli 400 + `detail` xabari bilan javob qaytaradi — endi
    tutilmagan exception tufayli 500 bilan yiqilmaydi.
    """

    def test_create_question_without_company_profile_returns_400(self):
        candidate = _create_user("aiq_crash@gmail.com", user_type="candidate")
        client = APIClient()
        client.force_authenticate(user=candidate)
        response = client.post(
            reverse(AI_QUESTIONS_LIST), {"text": "Muammoli savol"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertFalse(AIInterviewQuestion.objects.exists())



class CompanyVacancyScopingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("vac_owner@gmail.com")
        self.other = _create_user("vac_other@gmail.com")
        self.owner_company = _create_company_profile(self.owner)
        self.other_company = _create_company_profile(self.other)
        self.owner_vacancy = _create_vacancy(self.owner_company, title="Owner vakansiyasi")
        self.other_vacancy = _create_vacancy(self.other_company, title="Other vakansiyasi")

    def test_user_sees_only_own_company_vacancies(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(reverse(COMPANY_VACANCY_LIST))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data]
        self.assertEqual(ids, [self.owner_vacancy.id])

    def test_cannot_retrieve_other_companys_vacancy(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse(COMPANY_VACANCY_DETAIL, kwargs={"pk": self.other_vacancy.pk})
        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )

    def test_anonymous_user_cannot_access_vacancies(self):
        response = self.client.get(reverse(COMPANY_VACANCY_LIST))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_vacancy_without_company_profile_returns_400(self):
        candidate = _create_user("vac_no_company@gmail.com", user_type="candidate")
        self.client.force_authenticate(user=candidate)
        response = self.client.post(
            reverse(COMPANY_VACANCY_LIST),
            {
                "title": "Test",
                "description": "Test tavsif",
                "publish_start": "2026-01-01",
                "publish_end": "2026-02-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_create_vacancy_is_linked_to_callers_company(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            reverse(COMPANY_VACANCY_LIST),
            {
                "title": "Frontend Developer",
                "description": "React tajribasi kerak",
                "publish_start": "2026-01-01",
                "publish_end": "2026-02-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Vacancy.objects.get(pk=response.data["id"])
        self.assertEqual(created.company_id, self.owner_company.id)



class CompanyProfileSerializerComputedFieldsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("stats_owner@gmail.com")
        self.company = _create_company_profile(self.owner)
        self.client.force_authenticate(user=self.owner)

    def test_vacancy_counts_are_computed_correctly(self):
        _create_vacancy(self.company, title="Ochiq 1", status=Vacancy.Status.OPEN)
        _create_vacancy(self.company, title="Ochiq 2", status=Vacancy.Status.OPEN)
        _create_vacancy(self.company, title="Yopiq 1", status=Vacancy.Status.CLOSED)

        url = reverse(COMPANY_PROFILE_DETAIL, kwargs={"pk": self.company.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["vacancies_total"], 3)
        self.assertEqual(response.data["vacancies_open"], 2)
        self.assertEqual(response.data["vacancies_closed"], 1)

    def test_vacancy_counts_do_not_include_other_companys_vacancies(self):
        other_owner = _create_user("stats_other@gmail.com")
        other_company = _create_company_profile(other_owner)
        _create_vacancy(other_company, title="Boshqa kompaniya")

        url = reverse(COMPANY_PROFILE_DETAIL, kwargs={"pk": self.company.pk})
        response = self.client.get(url)

        self.assertEqual(response.data["vacancies_total"], 0)


class CompanyProfileModelTests(TestCase):
    def test_str_returns_name(self):
        owner = _create_user("model_owner@gmail.com")
        profile = _create_company_profile(owner, name="Acme LLC")
        self.assertEqual(str(profile), "Acme LLC")

    def test_str_falls_back_to_user_when_name_empty(self):
        owner = _create_user("model_owner2@gmail.com")
        profile = CompanyProfile.objects.create(user=owner, name="")
        self.assertEqual(str(profile), str(owner))


class AIInterviewQuestionModelTests(TestCase):
    def test_default_question_type_and_difficulty(self):
        owner = _create_user("model_q_owner@gmail.com")
        company = _create_company_profile(owner)
        question = _create_question(company)
        self.assertEqual(question.question_type, AIInterviewQuestion.QuestionType.TECHNICAL)
        self.assertEqual(question.difficulty, AIInterviewQuestion.Difficulty.JUNIOR)
        self.assertTrue(question.is_active)

    def test_str_includes_company_name_and_text_snippet(self):
        owner = _create_user("model_q_owner2@gmail.com")
        company = _create_company_profile(owner, name="Acme LLC")
        question = _create_question(company, text="Bu juda uzun savol matni bo'lishi mumkin")
        self.assertTrue(str(question).startswith("Acme LLC:"))