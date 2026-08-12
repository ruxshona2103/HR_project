from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.users1.models import User, TelegramLinkToken


class MeViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create(
            email="me@gmail.com",
            first_name="Ali",
            last_name="Valiyev",
            user_type="candidate",
        )
        self.user.set_password("StrongPass123!")
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Profilni ko'rish"""
        url = reverse('users1:me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "me@gmail.com")
        self.assertEqual(response.data['full_name'], "Valiyev Ali")

    def test_get_profile_requires_auth(self):
        """Login qilmagan foydalanuvchi profilni ko'ra olmaydi"""
        self.client.force_authenticate(user=None)
        url = reverse('users1:me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile_success(self):
        """Profilni tahrirlash"""
        url = reverse('users1:me')
        response = self.client.patch(url, {"first_name": "Vali"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Vali")

    def test_patch_profile_cannot_change_email(self):
        """Email — read_only, o'zgartirib bo'lmaydi"""
        url = reverse('users1:me')
        response = self.client.patch(url, {"email": "hacked@gmail.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "me@gmail.com")

    def test_patch_profile_duplicate_phone(self):
        """Boshqa userda bor telefon raqamni qo'yib bo'lmaydi"""
        User.objects.create(phone_number="+998901111111", user_type="candidate")
        url = reverse('users1:me')
        response = self.client.patch(url, {"phone_number": "+998901111111"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create(email="pw@gmail.com", user_type="candidate")
        self.user.set_password("OldPass123!")
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        url = reverse('users1:change-password')
        response = self.client.post(url, {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "new_password_confirm": "NewPass456!",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))

    def test_change_password_wrong_old_password(self):
        url = reverse('users1:change-password')
        response = self.client.post(url, {
            "old_password": "WrongOld!",
            "new_password": "NewPass456!",
            "new_password_confirm": "NewPass456!",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self):
        url = reverse('users1:change-password')
        response = self.client.post(url, {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "new_password_confirm": "Different!",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_requires_auth(self):
        self.client.force_authenticate(user=None)
        url = reverse('users1:change-password')
        response = self.client.post(url, {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "new_password_confirm": "NewPass456!",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create(email="logout@gmail.com", user_type="candidate")
        self.user.set_unusable_password()
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_logout_success(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        url = reverse('users1:logout')
        response = self.client.post(url, {"refresh": str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_missing_token(self):
        url = reverse('users1:logout')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalid_token(self):
        url = reverse('users1:logout')
        response = self.client.post(url, {"refresh": "not-a-real-token"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteAccountViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create(email="delete@gmail.com", user_type="candidate")
        self.user.set_unusable_password()
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_delete_account_success(self):
        url = reverse('users1:delete-account')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(email="delete@gmail.com").exists())

    def test_delete_account_requires_auth(self):
        self.client.force_authenticate(user=None)
        url = reverse('users1:delete-account')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BotLinkViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_bot_link_returns_url(self):
        url = reverse('users1:bot-link')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("bot_link", response.data)
        self.assertTrue(response.data["bot_link"].startswith("https://t.me/"))


class TelegramConnectViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create(email="tg@gmail.com", user_type="candidate")
        self.user.set_unusable_password()
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_get_requires_params(self):
        url = reverse('users1:telegram-connect')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_unknown_token_still_ready(self):
        """Token DBda topilmasa ham, chat_id bilan 'ready' javob qaytadi"""
        url = reverse('users1:telegram-connect')
        response = self.client.get(url, {"token": "unknown", "chat_id": "555"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ready")

    def test_get_valid_token(self):
        token = TelegramLinkToken.objects.create(
            token="abc123",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        url = reverse('users1:telegram-connect')
        response = self.client.get(url, {"token": "abc123", "chat_id": "555"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "valid")

    def test_get_expired_token(self):
        token = TelegramLinkToken.objects.create(
            token="expired123",
            expires_at=timezone.now() - timedelta(minutes=10),
        )
        url = reverse('users1:telegram-connect')
        response = self.client.get(url, {"token": "expired123", "chat_id": "555"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_connect_with_valid_token(self):
        TelegramLinkToken.objects.create(
            token="tok1",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        url = reverse('users1:telegram-connect')
        response = self.client.post(url, {"token": "tok1", "chat_id": "111"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token_obj = TelegramLinkToken.objects.get(token="tok1")
        self.assertTrue(token_obj.is_used)
        self.assertEqual(token_obj.user_id, self.user.id)

        self.user.refresh_from_db()
        self.assertEqual(self.user.chat_id, "111")

    def test_post_connect_without_token_row(self):
        """Token DBda bo'lmasa 400 Bad Request qaytarishi va chat_id saqlanmasligi kerak"""
        url = reverse('users1:telegram-connect')
        self.client.force_authenticate(user=self.user)

        data = {"token": "non_existent_fake_token", "chat_id": "999888777"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.chat_id, "999888777")

    def test_post_connect_releases_chat_id_from_other_user(self):
        """chat_id boshqa userda bo'lsa — haqiqiy token bilan bog'langanda boshqasidan tozalanadi"""
        other_user = User.objects.create(email="other@gmail.com", chat_id="222", user_type="candidate")

        token_obj = TelegramLinkToken.objects.create(
            token="valid_test_token_123",
            expires_at=timezone.now() + timedelta(minutes=10),
            is_used=False
        )

        url = reverse('users1:telegram-connect')
        self.client.force_authenticate(user=self.user)

        data = {"token": "valid_test_token_123", "chat_id": "222"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        other_user.refresh_from_db()
        self.assertIsNone(other_user.chat_id)
        self.user.refresh_from_db()
        self.assertEqual(self.user.chat_id, "222")

    def test_post_connect_requires_auth(self):
        self.client.force_authenticate(user=None)
        url = reverse('users1:telegram-connect')
        response = self.client.post(url, {"token": "x", "chat_id": "1"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TelegramDisconnectViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create(email="dc@gmail.com", chat_id="333", user_type="candidate")
        self.user.set_unusable_password()
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_disconnect_success(self):
        url = reverse('users1:telegram-disconnect')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.chat_id)


class TelegramStatusViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_status_linked(self):
        user = User.objects.create(email="linked@gmail.com", chat_id="444", user_type="candidate")
        user.set_unusable_password()
        user.save()
        self.client.force_authenticate(user=user)
        url = reverse('users1:telegram-status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_linked"])
        self.assertEqual(response.data["chat_id"], "444")

    def test_status_not_linked(self):
        user = User.objects.create(email="notlinked@gmail.com", user_type="candidate")
        user.set_unusable_password()
        user.save()
        self.client.force_authenticate(user=user)
        url = reverse('users1:telegram-status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_linked"])
        self.assertIsNone(response.data["chat_id"])