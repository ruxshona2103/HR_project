# apps/users/models/email_verification.py
from django.db import models
from django.utils import timezone
import random
import string


class EmailVerificationCode(models.Model):
    """Email verification uchun 6 raqamli kod"""
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    # Registration ma'lumotlari (tasdiqlashdan oldin saqlanadi)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    password = models.CharField(max_length=255)  # hashed
    user_type = models.CharField(max_length=20)  # candidate yoki organization

    # Organization uchun
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=150, blank=True, null=True)

    def is_expired(self):
        """5 daqiqadan keyin eskiradi"""
        return (timezone.now() - self.created_at).total_seconds() > 300

    @staticmethod
    def generate_code():
        """6 raqamli kod yaratadi"""
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"{self.email} - {self.code}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Email Verification Code"
        verbose_name_plural = "Email Verification Codes"