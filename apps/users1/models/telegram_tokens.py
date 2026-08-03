"""
apps/users1/models/telegram_tokens.py

Telegram bot bilan platformani bog'lash uchun tokenlar:
  - TelegramLinkToken  : Foydalanuvchi profilini botga ulash
  - AIInterviewToken   : AI intervyu sessiyasini botdan ochish
"""

from django.db import models
from django.utils import timezone
from django.conf import settings


class TelegramLinkToken(models.Model):
    """
    Foydalanuvchi platformadan «Telegramni ulash» tugmasini
    bosganda yaratiladi. Bot bu token orqali foydalanuvchi
    kimligini bilib, chat_id ni uning profiliga yozadi.

    Ishlatish tartibi:
        1. Bot /start da bir martalik token yaratadi
        2. Foydalanuvchiga havola yuboriladi:
               {PLATFORM_URL}/telegram/connect/?token=<token>&chat_id=<chat_id>
        3. Platforma tokenni tekshirib, User.chat_id ni yangilaydi
        4. Token «is_used = True» bo'ladi
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_link_tokens",
        null=True,
        blank=True,
        help_text="Agar token avvaldan mavjud foydalanuvchi uchun yaratilgan bo'lsa",
    )
    token = models.CharField(max_length=128, unique=True, db_index=True)
    chat_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Bot tomonidan uzatiladigan Telegram chat ID",
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "Telegram Havola Tokeni"
        verbose_name_plural = "Telegram Havola Tokenlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Token: {self.token[:12]}... | User: {self.user} | Used: {self.is_used}"

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired()

    def consume(self, chat_id: str):
        """
        Tokenni bir martalik ishlatish:
        chat_id ni user ga yozadi va tokeni «used» qilib belgilaydi.
        """
        if self.user:
            self.user.chat_id = chat_id
            self.user.save(update_fields=["chat_id"])

        self.is_used = True
        self.chat_id = chat_id
        self.save(update_fields=["is_used", "chat_id", "user"])


class AIInterviewToken(models.Model):
    """
    Botdan AI intervyuga o'tish uchun bir martalik token.

    Vakansiyada AI intervyu mavjud bo'lganda, foydalanuvchi
    botdagi havolani bosib to'g'ridan-to'g'ri platforma
    AI intervyu sahifasiga kiradi.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_interview_tokens",
    )
    vacancy = models.ForeignKey(
        "vacancies.Vacancy",
        on_delete=models.CASCADE,
        related_name="ai_interview_tokens",
        null=True,
        blank=True,
    )
    token = models.CharField(max_length=128, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "AI Intervyu Tokeni"
        verbose_name_plural = "AI Intervyu Tokenlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"AIToken: {self.token[:12]}... | User: {self.user}"

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired()