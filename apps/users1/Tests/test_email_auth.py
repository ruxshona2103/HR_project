from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from apps.users1.models import User, EmailVerificationCode


class EmailLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(email="test@gmail.com", user_type="candidate")
        self.user.set_password("StrongPass123!")
        self.user.save()

    def test_login_success(self):
        """To'g'ri email + parol bilan login"""
        url = reverse('users1:email-login')
        response = self.client.post(url, {
            "email": "test@gmail.com",
            "password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        """Noto'g'ri parol"""
        url = reverse('users1:email-login')
        response = self.client.post(url, {
            "email": "test@gmail.com",
            "password": "WrongPass!",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_email(self):
        """Mavjud bo'lmagan email"""
        url = reverse('users1:email-login')
        response = self.client.post(url, {
            "email": "notexist@gmail.com",
            "password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailRegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('apps.users1.serializers.email_auth.dns.resolver.resolve')
    @patch('apps.users1.serializers.email_auth.send_mail')
    def test_candidate_register_success(self, mock_mail, mock_dns):
        """Nomzod email orqali ro'yxatdan o'tish"""
        mock_dns.return_value = [True]
        url = reverse('users1:email-candidate-register')
        response = self.client.post(url, {
            "email": "newuser@gmail.com",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(EmailVerificationCode.objects.filter(email="newuser@gmail.com").exists())
        self.assertTrue(mock_mail.called)

    @patch('apps.users1.serializers.email_auth.dns.resolver.resolve')
    @patch('apps.users1.serializers.email_auth.send_mail')
    def test_verify_email_success(self, mock_mail, mock_dns):
        """Email kodni to'g'ri tasdiqlash — user yaratiladi"""
        mock_dns.return_value = [True]
        # Avval register
        url_register = reverse('users1:email-candidate-register')
        self.client.post(url_register, {
            "email": "verify@gmail.com",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        })

        # Kodni olish
        verification = EmailVerificationCode.objects.get(email="verify@gmail.com")

        # Verify
        url_verify = reverse('users1:email-verify')
        response = self.client.post(url_verify, {
            "email": "verify@gmail.com",
            "code": verification.code,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="verify@gmail.com").exists())
        self.assertIn("tokens", response.data)

    def test_verify_wrong_code(self):
        """Noto'g'ri kod"""
        EmailVerificationCode.objects.create(
            email="test@gmail.com",
            code="123456",
            first_name="Ali",
            last_name="Valiyev",
            password="hashed",
            user_type="candidate",
        )
        url = reverse('users1:email-verify')
        response = self.client.post(url, {
            "email": "test@gmail.com",
            "code": "000000",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_mismatch(self):
        """Parollar mos kelmasligi"""
        url = reverse('users1:email-candidate-register')
        response = self.client.post(url, {
            "email": "test2@gmail.com",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass!",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
