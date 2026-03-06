from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email kiritish majburiy!")
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model
    - username yo'q, email = asosiy identifikator
    - phone_number ixtiyoriy (telefon qism boshqa developer qiladi)
    """

    email = models.EmailField(
        unique=True,
        verbose_name="Email manzil",
        error_messages={"unique": "Bu email allaqachon ro'yxatdan o'tgan."},
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Ism",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Familiya",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Telefon raqam",
        help_text="Ixtiyoriy. Masalan: +998901234567",
        error_messages={"unique": "Bu telefon raqam allaqachon ro'yxatdan o'tgan."},
    )

    is_active = models.BooleanField(default=True, verbose_name="Faol")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Ro'yxatdan o'tgan sana")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else self.email

    def get_short_name(self):
        return self.first_name or self.email
