from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.resume.models import Aloqa, Konikma, Resume, Talim
from apps.users1.models import User


def resume_payload(**overrides):
    data = {
        "mutaxasislik": "Backend dasturlash",
        "lavozim": "Backend Developer",
        "men_haqimda": "Test uchun rezyume.",
    }
    data.update(overrides)
    return data


def ish_tajribasi_payload(**overrides):
    data = {
        "kompaniya_nomi": "ABC Company",
        "lavozim": "Backend Developer",
        "ish_turi": "tolik",
        "boshlanish_sanasi": "2022-01-01",
        "hozir_ishlayapman": True,
        "tavsif": "Django, DRF bilan backend ishlab chiqdim",
        "shahar": "Toshkent",
    }
    data.update(overrides)
    return data


def talim_payload(**overrides):
    data = {
        "muassasa_nomi": "TATU",
        "daraja": "bakalavr",
        "mutaxassislik": "Dasturiy injiniring",
        "boshlanish_yili": 2019,
        "hozir_oqiyapman": True,
    }
    data.update(overrides)
    return data


def sertifikat_payload(**overrides):
    data = {
        "nomi": "AWS Solutions Architect",
        "tashkilot": "Amazon",
        "berilgan_sana": "2023-06-01",
        "muddatsiz": True,
    }
    data.update(overrides)
    return data


class ResumeTestSetupMixin:
    def setUp(self):
        self.user = User.objects.create_user(
            email="user1@example.com", password="pass12345", user_type="candidate",
            first_name="Ali", last_name="Valiyev",
        )
        self.other_user = User.objects.create_user(
            email="user2@example.com", password="pass12345", user_type="candidate",
            first_name="Vali", last_name="Aliyev",
        )
        self.resume_url = reverse("resume")
        self.section_list_url = lambda section: reverse("section-list", args=[section])
        self.section_detail_url = lambda section, pk: reverse("section-detail", args=[section, pk])


class ResumeViewTests(ResumeTestSetupMixin, APITestCase):
    def test_anonymous_cannot_get_resume(self):
        response = self.client.get(self.resume_url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_anonymous_cannot_create_resume(self):
        response = self.client.post(self.resume_url, resume_payload(), format="json")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_get_returns_404_when_resume_missing(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.resume_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_resume_success(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.resume_url, resume_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Resume.objects.filter(foydalanuvchi=self.user).exists())

    def test_create_resume_duplicate_is_blocked(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.resume_url, resume_payload(), format="json")
        response = self.client.post(self.resume_url, resume_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Resume.objects.filter(foydalanuvchi=self.user).count(), 1)

    def test_get_resume_after_create_does_not_crash(self):
        """
        Regression test: mutaxasislik maydonida `choices` yo'q, shuning uchun
        avvalgi mutaxassislik_nomi (get_mutaxasislik_display) maydoni
        AttributeError bilan qulardi. Bu test shu holatni ushlab qoladi.
        """
        self.client.force_authenticate(self.user)
        self.client.post(self.resume_url, resume_payload(), format="json")
        response = self.client.get(self.resume_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lavozim"], "Backend Developer")
        self.assertNotIn("mutaxassislik_nomi", response.data)

    def test_update_resume_lavozim(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.resume_url, resume_payload(), format="json")
        response = self.client.put(self.resume_url, {"lavozim": "Senior Backend Developer"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lavozim"], "Senior Backend Developer")

    def test_create_resume_with_nested_aloqa(self):
        self.client.force_authenticate(self.user)
        payload = resume_payload(aloqa={"telefon": "+998901234567", "email": "ali@example.com"})
        response = self.client.post(self.resume_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resume = Resume.objects.get(foydalanuvchi=self.user)
        self.assertTrue(Aloqa.objects.filter(resume=resume, email="ali@example.com").exists())

    def test_update_resume_upserts_aloqa(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.resume_url, resume_payload(), format="json")
        response = self.client.put(
            self.resume_url,
            {"aloqa": {"telefon": "+998901112233", "email": "yangi@example.com"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resume = Resume.objects.get(foydalanuvchi=self.user)
        self.assertEqual(resume.aloqa.email, "yangi@example.com")

    def test_users_only_see_their_own_resume(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.resume_url, resume_payload(lavozim="User1 lavozimi"), format="json")

        self.client.force_authenticate(self.other_user)
        self.client.post(self.resume_url, resume_payload(lavozim="User2 lavozimi"), format="json")

        response = self.client.get(self.resume_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lavozim"], "User2 lavozimi")


class ResumeSectionListViewTests(ResumeTestSetupMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)
        self.client.post(self.resume_url, resume_payload(), format="json")

    def test_unknown_section_returns_404(self):
        response = self.client.get(self.section_list_url("nomavjud"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_konikmalar_empty(self):
        response = self.client.get(self.section_list_url("konikmalar"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_konikma_does_not_crash(self):
        """Regression: daraja_nomi (get_daraja_display) xatosi tuzatilganini tekshiradi."""
        payload = {"nom": "Python", "daraja": "yuqori", "kategoriya": "Dasturlash tillari"}
        response = self.client.post(self.section_list_url("konikmalar"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nom"], "Python")

    def test_create_tillar_does_not_crash(self):
        payload = {"til_nomi": "Ingliz tili", "daraja": "b2"}
        response = self.client.post(self.section_list_url("tillar"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_ish_tajribasi_without_end_or_current_fails(self):
        payload = ish_tajribasi_payload(hozir_ishlayapman=False, tugash_sanasi=None)
        response = self.client.post(self.section_list_url("ish-tajribasi"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ish_tajribasi_with_hozir_ishlayapman_succeeds(self):
        payload = ish_tajribasi_payload()
        response = self.client.post(self.section_list_url("ish-tajribasi"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("ish_turi_nomi", response.data)

    def test_create_ish_tajribasi_with_end_date_succeeds(self):
        payload = ish_tajribasi_payload(hozir_ishlayapman=False, tugash_sanasi="2023-01-01")
        response = self.client.post(self.section_list_url("ish-tajribasi"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_talim_without_end_year_or_current_fails(self):
        payload = talim_payload(hozir_oqiyapman=False, tugash_yili=None)
        response = self.client.post(self.section_list_url("talim"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_talim_with_hozir_oqiyapman_succeeds(self):
        response = self.client.post(self.section_list_url("talim"), talim_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_sertifikat_without_expiry_or_muddatsiz_fails(self):
        payload = sertifikat_payload(muddatsiz=False, amal_qilish_muddati=None)
        response = self.client.post(self.section_list_url("sertifikatlar"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_sertifikat_with_muddatsiz_succeeds(self):
        response = self.client.post(self.section_list_url("sertifikatlar"), sertifikat_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_anonymous_cannot_list_sections(self):
        anonymous_client = APIClient()
        response = anonymous_client.get(self.section_list_url("konikmalar"))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class ResumeSectionDetailViewTests(ResumeTestSetupMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)
        self.client.post(self.resume_url, resume_payload(), format="json")
        self.resume = Resume.objects.get(foydalanuvchi=self.user)
        self.konikma = Konikma.objects.create(resume=self.resume, nom="Django", daraja="orta")

    def test_get_single_entry(self):
        response = self.client.get(self.section_detail_url("konikmalar", self.konikma.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nom"], "Django")

    def test_get_nonexistent_entry_returns_404(self):
        response = self.client.get(self.section_detail_url("konikmalar", 999999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_entry(self):
        response = self.client.put(
            self.section_detail_url("konikmalar", self.konikma.id), {"nom": "FastAPI"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.konikma.refresh_from_db()
        self.assertEqual(self.konikma.nom, "FastAPI")

    def test_delete_entry(self):
        response = self.client.delete(self.section_detail_url("konikmalar", self.konikma.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Konikma.objects.filter(id=self.konikma.id).exists())

    def test_cannot_access_other_users_entry(self):
        """Boshqa foydalanuvchining rezyume bo'limiga kirish 404 qaytarishi kerak."""
        self.client.force_authenticate(self.other_user)
        self.client.post(self.resume_url, resume_payload(), format="json")

        response = self.client.get(self.section_detail_url("konikmalar", self.konikma.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_delete_other_users_entry(self):
        self.client.force_authenticate(self.other_user)
        self.client.post(self.resume_url, resume_payload(), format="json")

        response = self.client.delete(self.section_detail_url("konikmalar", self.konikma.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Konikma.objects.filter(id=self.konikma.id).exists())