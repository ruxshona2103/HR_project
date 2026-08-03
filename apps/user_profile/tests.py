"""
UserProfile — xavfsizlik (IDOR) va CRUD regression testlari
==============================================================

KONTEKST
--------
Xavfsizlik auditida CRITICAL #1 sifatida IDOR (Insecure Direct Object
Reference) aniqlangan edi: `UserProfileViewSet` da `queryset = UserProfile
.objects.all()` va faqat `IsAuthenticated` bo'lgani uchun, tizimga kirgan
IXTIYORIY foydalanuvchi boshqa har qanday foydalanuvchining profiliga
GET / PUT / PATCH / DELETE qila olar edi.

MUHIM TAXMIN (agar farq qilsa moslashtiring)
---------------------------------------------
Ushbu test fayli quyidagi tuzatish allaqachon amalga oshirilgan deb
taxmin qiladi:
    1. `UserProfile` modeliga foydalanuvchiga bog'lovchi maydon qo'shilgan:
           user = models.OneToOneField(settings.AUTH_USER_MODEL, ...)
       Agar sherigingiz maydonni boshqa nom bilan qo'shgan bo'lsa
       (masalan `owner`), quyidagi ikkita joyni almashtiring:
           - `_create_profile()` yordamchi funksiyasidagi `user=` argumenti
           - permission/queryset testlarida ishlatilayotgan mantiq o'zi
             view/permission tomonida bo'lgani uchun bu yerda o'zgartirish
             shart emas.
    2. View darajasida obyekt permission qo'shilgan (masalan
       `IsProfileOwner`) va/yoki `get_queryset()` faqat
       `request.user`ga tegishli profil(lar)ni qaytaradi — xuddi
       loyihadagi `IsVacancyOwnerOrReadOnly` patterniga o'xshab.

Agar bu tuzatish hali qilinmagan bo'lsa — bu testlar FAIL beradi.
Bu TO'G'RI xatti-harakat: testlar "qizil" (RED) holatda boshlanishi va
sherigingiz IDOR tuzatuvini tugatgach "yashil" (GREEN) bo'lishi kerak.

MUHIM: BU TESTLARNI YOZISHDAN OLDIN TUZATILGAN 2 TA BLOKLOVCHI XATO
---------------------------------------------------------------------
Testlarni ishga tushirishdan oldin quyidagi ikkita xato modulni hatto
import qilishga ham yo'l qo'ymas edi — ular shu commitda tuzatildi:

    1. models.py: `user = models.OneToOneField(...)` qavsi yopilmagan
       edi -> `SyntaxError: '(' was never closed`. Yopuvchi `)` qo'shildi.
    2. urls.py: `router.register(r'user_profile', UserProfileViewSet)`
       da `basename` berilmagan edi. UserProfileViewSet faqat
       `get_queryset()` metodini aniqlaydi, klass darajasidagi
       `.queryset` atributi yo'q — shu sababli DRF SimpleRouter
       basename'ni avtomatik aniqlay olmay `AssertionError` berardi.
       `basename='userprofile'` aniq ko'rsatildi (bu quyidagi
       LIST_URL_NAME / DETAIL_URL_NAME bilan mos).

URL NOMLARI HAQIDA
-------------------
`apps/user_profile/urls.py` da DRF DefaultRouter ishlatiladi va
`basename` aniq ko'rsatilmagan, shu sababli DRF uni model nomidan
avtomatik chiqaradi: `UserProfile` -> `userprofile`.
    - Ro'yxat:  reverse('userprofile-list')
    - Detail:   reverse('userprofile-detail', kwargs={'pk': profile.pk})
Agar loyihaning bosh urls.py faylida bu router alohida `namespace` bilan
`include()` qilingan bo'lsa (masalan `user_profile:userprofile-detail`),
quyidagi `LIST_URL_NAME` / `DETAIL_URL_NAME` konstantalarini shunga qarab
yangilang — testning qolgan qismini o'zgartirish shart emas.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.user_profile.models import UserProfile
from apps.users1.models import User

LIST_URL_NAME = "userprofile-list"
DETAIL_URL_NAME = "userprofile-detail"


def _create_user(email, user_type="candidate"):
    """Test uchun autentifikatsiyadan o'tgan foydalanuvchi yaratish."""
    user = User.objects.create(email=email, user_type=user_type)
    user.set_password("StrongPass123!")
    user.save()
    return user


def _create_profile(user, **overrides):
    """Berilgan foydalanuvchiga tegishli UserProfile yaratish."""
    data = dict(
        user=user,
        first_name="Ali",
        last_name="Valiyev",
        birth_date="2000-01-01",
        phone_number="+998901234567",
        university_name="TATU",
        degree="Bakalavr",
        course=2,
        field_of_study="Software Engineering",
    )
    data.update(overrides)
    return UserProfile.objects.create(**data)


class UserProfileOwnerAccessTests(TestCase):
    """Foydalanuvchi FAQAT o'z profiliga to'liq (CRUD) ruxsatga ega bo'lishi kerak."""

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("owner@gmail.com")
        self.profile = _create_profile(self.owner)
        self.client.force_authenticate(user=self.owner)

    def test_owner_can_retrieve_own_profile(self):
        url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.profile.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.profile.id)

    def test_owner_can_update_own_profile_via_put(self):
        url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.profile.pk})
        payload = {
            "first_name": "Vali",
            "last_name": "Aliyev",
            "birth_date": "1999-05-05",
            "phone_number": "+998907654321",
            "university_name": "TDTU",
            "degree": "Magistr",
            "course": 1,
            "field_of_study": "Data Science",
        }
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.first_name, "Vali")

    def test_owner_can_partially_update_own_profile(self):
        url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.profile.pk})
        response = self.client.patch(url, {"course": 4}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.course, 4)

    def test_owner_can_delete_own_profile(self):
        url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.profile.pk})
        response = self.client.delete(url)
        self.assertIn(
            response.status_code,
            (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK),
        )
        self.assertFalse(UserProfile.objects.filter(pk=self.profile.pk).exists())


class UserProfileIDORRegressionTests(TestCase):
    """
    CRITICAL #1 IDOR uchun regression testlari.

    Maqsad: audit paytida topilgan xavfsizlik zaifligi qayta chiqmasligini
    kafolatlash — boshqa foydalanuvchining profiliga hech qanday
    operatsiya (GET/PUT/PATCH/DELETE) muvaffaqiyatli bo'lmasligi kerak.
    """

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("owner@gmail.com")
        self.attacker = _create_user("attacker@gmail.com")

        self.owner_profile = _create_profile(
            self.owner,
            first_name="Owner",
            last_name="Original",
            phone_number="+998901111111",
        )

        self.client.force_authenticate(user=self.attacker)
        self.url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.owner_profile.pk})

    def test_authenticated_user_cannot_retrieve_others_profile(self):
        """GET boshqa profilga -> 403 yoki 404, hech qachon 200 emas."""
        response = self.client.get(self.url)
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )

    def test_authenticated_user_cannot_update_others_profile_via_put(self):
        """PUT boshqa profilga -> 403/404 va ma'lumot bazada o'zgarmasligi kerak."""
        malicious_payload = {
            "first_name": "Hacked",
            "last_name": "Hacked",
            "birth_date": "2000-01-01",
            "phone_number": "+998909999999",
            "university_name": "N/A",
            "degree": "N/A",
            "course": 1,
            "field_of_study": "N/A",
        }
        response = self.client.put(self.url, malicious_payload, format="json")
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )

        self.owner_profile.refresh_from_db()
        self.assertEqual(self.owner_profile.first_name, "Owner")
        self.assertEqual(self.owner_profile.phone_number, "+998901111111")

    def test_authenticated_user_cannot_partially_update_others_profile(self):
        """PATCH boshqa profilga -> 403/404 va ma'lumot o'zgarmasligi kerak."""
        response = self.client.patch(self.url, {"course": 99}, format="json")
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )
        self.owner_profile.refresh_from_db()
        self.assertNotEqual(self.owner_profile.course, 99)

    def test_authenticated_user_cannot_delete_others_profile(self):
        """DELETE boshqa profilga -> 403/404 va profil bazada qolishi kerak."""
        response = self.client.delete(self.url)
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )
        self.assertTrue(UserProfile.objects.filter(pk=self.owner_profile.pk).exists())

    def test_list_endpoint_does_not_leak_other_users_profiles(self):
        """
        Ro'yxat endpoint'i orqali ham IDOR sodir bo'lishi mumkin: agar
        `get_queryset()` filtrlanmagan bo'lsa, attacker /user_profile/
        so'rovi bilan barcha foydalanuvchilarning profillarini ko'rishi
        mumkin. Bu yerda faqat o'z profili (agar mavjud bo'lsa) qaytishi
        yoki umuman owner_profile ro'yxatda ko'rinmasligi tekshiriladi.
        """
        list_url = reverse(LIST_URL_NAME)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data
        if isinstance(results, dict) and "results" in results:
            results = results["results"]

        returned_ids = {item["id"] for item in results}
        self.assertNotIn(
            self.owner_profile.id,
            returned_ids,
            "IDOR: boshqa foydalanuvchining profili ro'yxatda ko'rinmoqda!",
        )


class UserProfileAuthenticationRequiredTests(TestCase):
    """Autentifikatsiyasiz foydalanuvchi hech narsaga kira olmasligi kerak."""

    def setUp(self):
        self.client = APIClient()
        owner = _create_user("owner2@gmail.com")
        self.profile = _create_profile(owner)

    def test_anonymous_user_cannot_list_profiles(self):
        response = self.client.get(reverse(LIST_URL_NAME))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_retrieve_profile(self):
        url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.profile.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_delete_profile(self):
        url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.profile.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(UserProfile.objects.filter(pk=self.profile.pk).exists())


class UserProfileValidationTests(TestCase):
    """Profil yaratish/yangilashda asosiy validatsiya (regression sifatida)."""

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("owner3@gmail.com")
        self.client.force_authenticate(user=self.owner)

    def test_create_profile_missing_required_field_returns_400(self):
        url = reverse(LIST_URL_NAME)
        payload = {
            "last_name": "Valiyev",
            "birth_date": "2000-01-01",
            "phone_number": "+998901234567",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", response.data)

    def test_nonexistent_profile_returns_404(self):
        url = reverse(DETAIL_URL_NAME, kwargs={"pk": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_profile_with_negative_course_returns_400(self):
        """course PositiveSmallIntegerField -> manfiy qiymat qabul qilinmasligi kerak."""
        url = reverse(LIST_URL_NAME)
        payload = {
            "first_name": "Ali",
            "last_name": "Valiyev",
            "birth_date": "2000-01-01",
            "phone_number": "+998901234567",
            "course": -1,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("course", response.data)

    def test_create_profile_with_too_long_phone_number_returns_400(self):
        """phone_number max_length=15 -> undan uzun qiymat rad etilishi kerak."""
        url = reverse(LIST_URL_NAME)
        payload = {
            "first_name": "Ali",
            "last_name": "Valiyev",
            "birth_date": "2000-01-01",
            "phone_number": "+99890123456789999",  # 19 ta belgi
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

    def test_create_profile_with_invalid_birth_date_returns_400(self):
        url = reverse(LIST_URL_NAME)
        payload = {
            "first_name": "Ali",
            "last_name": "Valiyev",
            "birth_date": "not-a-date",
            "phone_number": "+998901234567",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("birth_date", response.data)

    def test_create_profile_with_valid_payload_succeeds(self):
        url = reverse(LIST_URL_NAME)
        payload = {
            "first_name": "Ali",
            "last_name": "Valiyev",
            "birth_date": "2000-01-01",
            "phone_number": "+998901234567",
            "university_name": "TATU",
            "degree": "Bakalavr",
            "course": 2,
            "field_of_study": "Software Engineering",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = UserProfile.objects.get(pk=response.data["id"])
        self.assertEqual(created.user_id, self.owner.id)


class UserProfileDuplicateCreationTests(TestCase):
    """Bitta foydalanuvchi uchun faqat bitta profil yaratilishi mumkin (perform_create qoidasi)."""

    def setUp(self):
        self.client = APIClient()
        self.owner = _create_user("owner4@gmail.com")
        self.client.force_authenticate(user=self.owner)
        self.existing_profile = _create_profile(self.owner)

    def test_owner_cannot_create_second_profile(self):
        url = reverse(LIST_URL_NAME)
        payload = {
            "first_name": "Ikkinchi",
            "last_name": "Profil",
            "birth_date": "2001-02-02",
            "phone_number": "+998901112233",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(
            UserProfile.objects.filter(user=self.owner).count(), 1
        )

    def test_anonymous_user_cannot_create_profile(self):
        self.client.force_authenticate(user=None)
        url = reverse(LIST_URL_NAME)
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileModelTests(TestCase):
    """Model darajasidagi (HTTP qatlamisiz) sof unit testlar."""

    def test_str_returns_full_name(self):
        user = _create_user("staff@gmail.com")
        profile = _create_profile(user, first_name="Ism", last_name="Familiya")
        self.assertEqual(str(profile), "Ism Familiya")

    def test_is_used_defaults_to_false(self):
        user = _create_user("staff2@gmail.com")
        profile = _create_profile(user)
        self.assertFalse(profile.is_used)

    def test_one_to_one_constraint_prevents_second_profile_at_db_level(self):
        """
        OneToOneField `user` maydonini himoya qiladi: bitta foydalanuvchiga
        ikkinchi profilni to'g'ridan-to'g'ri ORM orqali yaratishga urinish
        ham IntegrityError berishi kerak (API qatlamidan mustaqil himoya).
        """
        from django.db import IntegrityError, transaction

        user = _create_user("staff3@gmail.com")
        _create_profile(user)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                _create_profile(user, phone_number="+998900000000")


class IsProfileOwnerPermissionUnitTests(TestCase):
    """
    `IsProfileOwner.has_object_permission` ni HTTP/URL qatlamisiz,
    to'g'ridan-to'g'ri chaqirib tekshiruvchi sof unit testlar.
    """

    def setUp(self):
        from apps.user_profile.permissions import IsProfileOwner
        from django.test import RequestFactory

        self.permission = IsProfileOwner()
        self.factory = RequestFactory()
        self.owner = _create_user("perm_owner@gmail.com")
        self.other = _create_user("perm_other@gmail.com")
        self.profile = _create_profile(self.owner)

    def _request_for(self, user):
        django_request = self.factory.get("/fake-url/")
        django_request.user = user
        return django_request

    def test_owner_has_object_permission(self):
        request = self._request_for(self.owner)
        self.assertTrue(
            self.permission.has_object_permission(request, view=None, obj=self.profile)
        )

    def test_non_owner_does_not_have_object_permission(self):
        request = self._request_for(self.other)
        self.assertFalse(
            self.permission.has_object_permission(request, view=None, obj=self.profile)
        )

    def test_anonymous_user_does_not_have_object_permission(self):
        from django.contrib.auth.models import AnonymousUser

        request = self._request_for(AnonymousUser())
        self.assertFalse(
            self.permission.has_object_permission(request, view=None, obj=self.profile)
        )