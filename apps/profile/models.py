from django.conf import settings
from django.db import models


class CompanyProfile(models.Model):
    """
    Tashkilot (kompaniya) profili.

    Employer roliga ega foydalanuvchi uchun bitta kompaniya profili
    bo'lishi nazarda tutilgan.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_profile",
    )
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company profile"
        verbose_name_plural = "Company profiles"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name or str(self.user)


class AIInterviewQuestion(models.Model):
    """
    Har bir kompaniya uchun AI interview savollari.
    """

    class Difficulty(models.TextChoices):
        JUNIOR = "junior", "Junior"
        MIDDLE = "middle", "Middle"
        SENIOR = "senior", "Senior"

    class QuestionType(models.TextChoices):
        TECHNICAL = "technical", "Technical"
        HR = "hr", "HR"
        BEHAVIORAL = "behavioral", "Behavioral"

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="ai_questions",
    )
    text = models.TextField()
    question_type = models.CharField(
        max_length=32,
        choices=QuestionType.choices,
        default=QuestionType.TECHNICAL,
    )
    difficulty = models.CharField(
        max_length=16,
        choices=Difficulty.choices,
        default=Difficulty.JUNIOR,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "AI interview question"
        verbose_name_plural = "AI interview questions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.company.name}: {self.text[:50]}"

