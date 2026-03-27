from django.db import models
from django.utils import timezone
from .user import phone_regex


class OTPCode(models.Model):
    """
    Telegram bot tomonidan yoziladigan OTP kod.
    Bot foydalanuvchiga Telegram orqali kod yuboradi va shu yerga saqlaydi.
    Web sayt esa shu kodni tekshiradi.
    """
    phone_number = models.CharField(max_length=15, validators=[phone_regex])
    chat_id = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        """5 daqiqadan (300 soniya) keyin kod eskiradi"""
        return (timezone.now() - self.created_at).total_seconds() > 300

    def __str__(self):
        return f"{self.phone_number} - {self.code}"

    class Meta:
        verbose_name = "OTP Kod"
        verbose_name_plural = "OTP Kodlar"
        ordering = ['-created_at']


class PendingRegistration(models.Model):
    """
    Telefon orqali ro'yxat — OTP tasdiqlashdan OLDIN
    foydalanuvchi ma'lumotlari vaqtincha shu yerda saqlanadi.
    OTP tasdiqlangandan so'ng User yaratiladi va bu yozuv o'chiriladi.
    """
    phone_number = models.CharField(max_length=15, unique=True)
    user_type = models.CharField(max_length=20)

    # Candidate uchun
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True)

    # Organization uchun
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=150, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        """10 daqiqada tasdiqlash kerak"""
        return (timezone.now() - self.created_at).total_seconds() > 600

    def __str__(self):
        return f"{self.phone_number} ({self.user_type})"

    class Meta:
        verbose_name = "Kutilayotgan Ro'yxat"
        verbose_name_plural = "Kutilayotgan Ro'yxatlar"
