from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import UserRole, UserProfile


# from resume.models import Resume  # rezyume modeli tayyor bolganda import qilinadi

class SetUserRoleAction:
    def __init__(self, user, role):
        self.user = user
        self.role = role

    def execute(self):
        with transaction.atomic():
            # Profilni olamiz yoki yaratamiz, keyin rolni yangilaymiz
            profile, created = UserProfile.objects.get_or_create(user=self.user)
            # Agar foydalanuvchi allaqachon rol tanlagan bo‘lsa, xato qaytaramiz
            if profile.role:
                raise ValidationError("Siz allaqachon rol tanlagansiz va uni o'zgartira olmaysiz.")

            profile.role = self.role
            profile.save()

            # Rolga qarab qo‘shimcha obyekt yaratish
            self._create_related_profile(profile)

    def _create_related_profile(self, profile):
        """
        Tanlangan rolga qarab tegishli jadvallarda yozuv yaratadi.
        Nomzod uchun Resume modeli OneToOne orqali yaratiladi.
        """
        if self.role == UserRole.CANDIDATE:
            # Resume.objects.create(user=self.user) # Resume modeli tayyor bo'lganda commentdan ochish kerak
            pass
        elif self.role == UserRole.EMPLOYER:
            # EmployerProfile.objects.create(user=self.user)# Ish beruvchi profili
            pass