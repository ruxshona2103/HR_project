from django.db import models
from django.utils import timezone


class OTPAttempt(models.Model):
    """ Xar no'to'g'ri urinish saqlanadi """
    phone_number = models.CharField(max_length=15)
    attempts = models.IntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(auto_now=True)

    def is_blocked(self):
        """Blocklanganmi yo'qmi tekshiradi"""
        if self.blocked_until and timezone.now() < self.blocked_until:
            return True
        return False

    def add_attempt(self):
        """5 marta xato qilganda block qiladi"""
        self.attempts += 1
        if self.attempts >= 5:
            self.blocked_until = timezone.now() + timezone.timedelta(minutes=10)
        self.save()

    def reset(self):
        """Kod to'g'ri bo'lganda tozalaydi"""
        self.attempts = 0
        self.blocked_until = None
        self.save()

    def __str__(self):
        return f"{self.phone_number} - {self.attempts} attempts"


