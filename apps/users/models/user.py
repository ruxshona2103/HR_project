from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator
from rest_framework.response import Response

phone_regex = RegexValidator(
    regex=r'^\+\d{10,15}$',
    message="Telefon raqam to'g'ri formatda bo'lishi kerak."
)


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError('Email yoki telefon raqam kiritilishi shart')

        # Bittasi bo'sh bo'lsa — ikkinchisini USERNAME_FIELD ga qo'yamiz
        if not email:
            email = None

        if email:
            email = self.normalize_email(email).lower()

        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('candidate', 'Nomzod'),
        ('organization', 'Tashkilot'),
    ]

    # Asosiy maydonlar
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        validators=[phone_regex]
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, null=True, blank=True)

    # Umumiy maydonlar
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True, verbose_name="Sharif")

    # Tashkilot uchun
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=150, blank=True, null=True, verbose_name="Lavozim")

    # Telegram uchun
    chat_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    # Email yoki phone bilan login
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return self.email or self.phone_number or f"User {self.id}"

    def get_full_name(self):
        if self.user_type == 'organization':
            return self.organization_name or self.email
        full = f"{self.last_name} {self.first_name} {self.middle_name}".strip()
        return full if full else (self.email or self.phone_number)

