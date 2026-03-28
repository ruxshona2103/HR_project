from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Soha (IT, Tibbiyot, Ta'lim va h.k.)"""
    name = models.CharField(max_length=100, verbose_name="Soha nomi")

    class Meta:
        verbose_name = "Soha"
        verbose_name_plural = "Sohalar"

    def __str__(self):
        return self.name


class Vacancy(models.Model):
    """Vakansiya (Ish e'loni)"""

    CITY_CHOICES = [
        ('toshkent', 'Toshkent'),
        ('samarqand', 'Samarqand'),

    ]

    title = models.CharField(max_length=200, verbose_name="Lavozim nomi")
    company = models.CharField(max_length=200, verbose_name="Kompaniya nomi")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, related_name='vacancies',
        verbose_name="Soha"
    )
    city = models.CharField(
        max_length=50, choices=CITY_CHOICES,
        verbose_name="Shahar"
    )
    salary_min = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Minimal maosh ($)"
    )
    salary_max = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Maksimal maosh ($)"
    )
    description = models.TextField(verbose_name="Tavsif")
    requirements = models.TextField(
        blank=True,
        verbose_name="Talablar"
    )
    is_active = models.BooleanField(default=True, verbose_name="Faolmi?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vakansiya"
        verbose_name_plural = "Vakansiyalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.company}"

    @property
    def salary_range(self):
        if self.salary_min and self.salary_max:
            return f"${self.salary_min} - ${self.salary_max}"
        elif self.salary_min:
            return f"${self.salary_min}+"
        return "Kelishuv asosida"


class Resume(models.Model):
    """Nomzod rezyumesi"""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='resume',
        verbose_name="Foydalanuvchi"
    )
    full_name = models.CharField(max_length=200, verbose_name="To'liq ism")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    email = models.EmailField(verbose_name="Email")
    skills = models.TextField(verbose_name="Ko'nikmalar")
    experience = models.TextField(blank=True, verbose_name="Ish tajribasi")
    education = models.TextField(blank=True, verbose_name="Ta'lim")
    resume_file = models.FileField(
        upload_to='resumes/',
        null=True, blank=True,
        verbose_name="Resume fayli (PDF)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rezyume"
        verbose_name_plural = "Rezyumalar"

    def __str__(self):
        return f"{self.full_name} — rezyume"


class Application(models.Model):
    """Ariza (nomzod vakansiyaga topshirgan)"""

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('reviewed', "Ko'rib chiqildi"),
        ('accepted', 'Qabul qilindi'),
        ('rejected', 'Rad etildi'),
    ]

    vacancy = models.ForeignKey(
        Vacancy, on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Vakansiya"
    )
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Rezyume"
    )
    cover_letter = models.TextField(
        blank=True,
        verbose_name="Motivatsion xat"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Holat"
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ariza"
        verbose_name_plural = "Arizalar"
        unique_together = ('vacancy', 'resume')  # bir vakansiyaga bir marta ariza
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.resume.full_name} → {self.vacancy.title}"