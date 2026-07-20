from django.db import models
from django.utils import timezone


class OTPAttempt(models.Model):
    """
    Telefon raqam bo'yicha noto'g'ri OTP urinishlarini hisoblaydi.
    5 marta xato qilsa — 10 daqiqa bloklanadi.
    """
    phone_number = models.CharField(max_length=15, unique=True)
    attempts = models.IntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(auto_now=True)

    def is_blocked(self):
        """Hozir bloklangan yoki yo'qligini tekshiradi"""
        if self.blocked_until and timezone.now() < self.blocked_until:
            return True
        return False

    def add_attempt(self):
        """Xato urinish qo'shadi. 5 martadan keyin bloklanadi."""
        self.attempts += 1
        if self.attempts >= 5:
            self.blocked_until = timezone.now() + timezone.timedelta(minutes=10)
        self.save()

    def reset(self):
        """Kod to'g'ri bo'lganda — urinishlar tozalanadi"""
        self.attempts = 0
        self.blocked_until = None
        self.save()

    def __str__(self):
        return f"{self.phone_number} - {self.attempts} urinish"

    class Meta:
        verbose_name = "OTP Urinish"
        verbose_name_plural = "OTP Urinishlar"
