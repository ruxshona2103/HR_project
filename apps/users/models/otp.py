from django.db import models
from django.utils import timezone
from .user import phone_regex


class OTPCode(models.Model):
    """Vaqtinchalik — bot telefon olganda shu modelga yozadi
    Web sayt shu kodni tekshiradi"""
    phone_number = models.CharField(max_length=13, validators=[phone_regex])
    chat_id = models.CharField(max_length=20)
    username = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        """ 60 sekunddan keyin kod eskiradi """
        return (timezone.now() - self.created_at).total_seconds() > 60

    def __str__(self):
        return f"{self.phone_number} - {self.code}"


class EmailOTPCode(models.Model):
    """Email orqali yuborilgan OTP kodlar"""
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 300  # 5 daqiqa

    def __str__(self):
        return f"{self.email} - {self.code}"


class PendingRegistration(models.Model):
    """Telefon orqali ro'yxat — OTP kutilayotgan ma'lumotlar"""
    phone_number = models.CharField(max_length=15, unique=True)
    user_type = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=255)  # hashed parol

    # Candidate uchun
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True)

    # Organization uchun
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=150, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # 10 daqiqada tasdiqlash kerak
        return (timezone.now() - self.created_at).total_seconds() > 600