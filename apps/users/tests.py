from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from unittest.mock import patch
from apps.users.models import User, OTPCode, OTPAttempt
from django.test import override_settings
from django.test import TestCase, override_settings


@override_settings(TESTING=True)
class VerifyOTPTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('verify-otp')

        self.phone = '+998901234567'
        self.code = '123456'
        self.otp = OTPCode.objects.create(
            phone_number=self.phone,
            chat_id='123456789',
            username='test_user',
            code=self.code,
            is_used=False
        )

    def test_verify_otp_success(self):
        """To'g'ri kod — JWT token qaytarishi kerak"""
        response = self.client.post(self.url, {
            'phone_number': self.phone,
            'code': self.code
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_verify_otp_wrong_code(self):
        """Noto'g'ri kod — 400 qaytarishi kerak"""
        response = self.client.post(self.url, {
            'phone_number': self.phone,
            'code': '000000'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_verify_otp_expired(self):
        """Eskirgan kod — 400 qaytarishi kerak"""
        self.otp.created_at = timezone.now() - timezone.timedelta(seconds=61)
        self.otp.save()

        response = self.client.post(self.url, {
            'phone_number': self.phone,
            'code': self.code
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_used_code(self):
        """Ishlatilgan kod — 400 qaytarishi kerak"""
        self.otp.is_used = True
        self.otp.save()

        response = self.client.post(self.url, {
            'phone_number': self.phone,
            'code': self.code
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_invalid_phone(self):
        """Noto'g'ri telefon format — 400 qaytarishi kerak"""
        response = self.client.post(self.url, {
            'phone_number': 'abc123',
            'code': self.code
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_user_created(self):
        """Yangi user yaratilishi kerak"""
        response = self.client.post(self.url, {
            'phone_number': self.phone,
            'code': self.code
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(phone_number=self.phone).exists())

    def test_existing_user_login(self):
        """Mavjud user login qilishi kerak"""
        User.objects.create_user(phone_number=self.phone)

        response = self.client.post(self.url, {
            'phone_number': self.phone,
            'code': self.code
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Muvaffaqiyatli kirildi')


@override_settings(TESTING=True)
class BruteForceTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('verify-otp')
        self.phone = '+998901234567'

        OTPCode.objects.create(
            phone_number=self.phone,
            chat_id='123456789',
            username='test_user',
            code='123456',
            is_used=False
        )

    def test_brute_force_blocked_after_5_attempts(self):
        """5 marta xato — bloklashi kerak"""
        for i in range(5):
            self.client.post(self.url, {
                'phone_number': self.phone,
                'code': '000000'
            }, format='json')

        """ Endi blocklashi kk """
        response = self.client.post(self.url, {
            'phone_number': self.phone,
            'code': '000000'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('bloklangan', response.data['error'])

    def test_correct_code_resets_attempts(self):
        """To'g'ri kod — urinishlarni tozalashi kerak. Boshida 3 ta xato code kiritamiz"""

        for i in range(3):
            self.client.post(self.url, {
                'phone_number': self.phone,
                'code': '000000'
            }, format='json')


        self.client.post(self.url, {
            'phone_number': self.phone,
            'code': '123456'
        }, format='json')

        attempt = OTPAttempt.objects.get(phone_number=self.phone)
        self.assertEqual(attempt.attempts, 0)
        self.assertIsNone(attempt.blocked_until)


@override_settings(TESTING=True)
class LogoutTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.logout_url = reverse('logout')
        self.verify_url = reverse('verify-otp')
        self.phone = '+998901234567'

        OTPCode.objects.create(
            phone_number=self.phone,
            chat_id='123456789',
            username='test_user',
            code='123456',
            is_used=False
        )

    def _get_tokens(self):
        """Login qilib token olish"""
        response = self.client.post(self.verify_url, {
            'phone_number': self.phone,
            'code': '123456'
        }, format='json')
        return response.data['tokens']

    def test_logout_success(self):
        """Logout muvaffaqiyatli ishlashi kerak"""
        tokens = self._get_tokens()

        response = self.client.post(self.logout_url, {
            'refresh': tokens['refresh']
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_invalid_token(self):
        """Noto'g'ri token — 400 qaytarishi kerak"""
        response = self.client.post(self.logout_url, {
            'refresh': 'notugri_token'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(TESTING=True)
class MeViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.me_url = reverse('me')
        self.verify_url = reverse('verify-otp')
        self.phone = '+998901234567'

        OTPCode.objects.create(
            phone_number=self.phone,
            chat_id='123456789',
            username='test_user',
            code='123456',
            is_used=False
        )

    def _login(self):
        """Login qilib access token olish"""
        response = self.client.post(self.verify_url, {
            'phone_number': self.phone,
            'code': '123456'
        }, format='json')
        access = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    def test_me_authenticated(self):
        """Login bo'lgan user profil ko'ra olishi kerak"""
        self._login()
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], self.phone)

    def test_me_unauthenticated(self):
        """Login bo'lmagan user — 401 olishi kerak"""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch_name(self):
        """Ism o'zgartirish ishlashi kerak"""
        self._login()
        response = self.client.patch(self.me_url, {
            'name': 'Yangi Ism'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Yangi Ism')

    def test_me_patch_phone_readonly(self):
        """Telefon raqam o'zgartirib bo'lmasligi kerak"""
        self._login()
        response = self.client.patch(self.me_url, {
            'phone_number': '+998999999999'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], self.phone)