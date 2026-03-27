from django.db import models
from django.utils import timezone
import random
import string


class EmailVerificationCode(models.Model):
    """
    Email orqali ro'yxat — OTP tasdiqlashdan OLDIN
    foydalanuvchi ma'lumotlari vaqtincha shu yerda saqlanadi.
    Kod emailga yuboriladi. Tasdiqlangach User yaratiladi.
    """
    email = models.EmailField()
    code = models.CharField(max_length=6)

    """Foydalanuvchi ma'lumotlari (tasdiqlashdan oldingi..)"""
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    password = models.CharField(max_length=255)  # hashed parol
    user_type = models.CharField(max_length=20)

    """Tashkilotniki"""
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=150, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        """5 daqiqadan keyin eskiradi"""
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    @staticmethod
    def generate_code():
        """6 raqamli tasdiqlash kodi"""
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"{self.email} - {self.code}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Email Tasdiqlash Kodi"
        verbose_name_plural = "Email Tasdiqlash Kodlari"
