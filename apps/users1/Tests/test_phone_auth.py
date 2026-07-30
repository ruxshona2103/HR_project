from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users1.models import User, OTPCode, PendingRegistration, OTPAttempt
from django.conf import settings
settings.PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

class PhoneRegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_candidate_register_success(self):
        """Nomzod muvaffaqiyatli ro'yxatdan o'tishi"""
        url = reverse('users1:phone-candidate-register')
        data = {
            "phone_number": "+998901234567",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "middle_name": "Akbarovich",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PendingRegistration.objects.filter(phone_number="+998901234567").exists())

    def test_candidate_register_duplicate_phone(self):
        """Allaqachon ro'yxatdan o'tgan telefon raqam"""
        User.objects.create(phone_number="+998901234567", user_type="candidate")
        url = reverse('users1:phone-candidate-register')
        data = {
            "phone_number": "+998901234567",
            "first_name": "Ali",
            "last_name": "Valiyev",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_organization_register_success(self):
        """Tashkilot muvaffaqiyatli ro'yxatdan o'tishi"""
        url = reverse('users1:phone-organization-register')
        data = {
            "phone_number": "+998901234568",
            "first_name": "Vali",
            "last_name": "Valiyev",
            "organization_name": "ABC Company",
            "position": "HR",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending = PendingRegistration.objects.get(phone_number="+998901234568")
        self.assertEqual(pending.user_type, "organization")


class OTPVerifyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.phone = "+998901234567"

    def _create_otp(self, code="123456"):
        return OTPCode.objects.create(
            phone_number=self.phone,
            chat_id="12345678",
            code=code,
        )

    def test_verify_otp_login(self):
        """Mavjud user OTP bilan login qiladi"""
        user = User.objects.create(phone_number=self.phone, user_type="candidate")
        user.set_unusable_password()
        user.save()
        self._create_otp()

        url = reverse('users1:phone-verify-otp')
        response = self.client.post(url, {"phone_number": self.phone, "code": "123456"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)

    def test_verify_otp_register(self):
        """PendingRegistration dan yangi user yaratiladi"""
        PendingRegistration.objects.create(
            phone_number=self.phone,
            user_type="candidate",
            first_name="Ali",
            last_name="Valiyev",
        )
        self._create_otp()

        url = reverse('users1:phone-verify-otp')
        response = self.client.post(url, {"phone_number": self.phone, "code": "123456"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(phone_number=self.phone).exists())

    def test_verify_otp_wrong_code(self):
        """Noto'g'ri kod — xato qaytadi"""
        self._create_otp("654321")
        url = reverse('users1:phone-verify-otp')
        response = self.client.post(url, {"phone_number": self.phone, "code": "000000"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_blocked(self):
        """5 marta xato — bloklanadi"""
        from django.utils import timezone
        attempt = OTPAttempt.objects.create(
            phone_number=self.phone,
            attempts=5,
            blocked_until=timezone.now() + timezone.timedelta(minutes=10),
        )
        self._create_otp()
        url = reverse('users1:phone-verify-otp')
        response = self.client.post(url, {"phone_number": self.phone, "code": "123456"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
