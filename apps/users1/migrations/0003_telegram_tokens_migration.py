"""
Migration: TelegramLinkToken va AIInterviewToken modellarini yaratish
Faylni: apps/users1/migrations/ papkasiga qo'ying va nomini moslashtiring
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users1", "0002_initial"),
        ("vacancies", "0004_vacancy_company"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramLinkToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(db_index=True, max_length=128, unique=True)),
                ("chat_id", models.CharField(blank=True, max_length=20, null=True)),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="telegram_link_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Telegram Havola Tokeni",
                "verbose_name_plural": "Telegram Havola Tokenlari",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AIInterviewToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(db_index=True, max_length=128, unique=True)),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_interview_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vacancy",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_interview_tokens",
                        to="vacancies.vacancy",
                    ),
                ),
            ],
            options={
                "verbose_name": "AI Intervyu Tokeni",
                "verbose_name_plural": "AI Intervyu Tokenlari",
                "ordering": ["-created_at"],
            },
        ),
    ]
