from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r'^\+\d{10,15}$',
    message="Telefon raqam to'g'ri formatda bo'lishi kerak. Masalan: +998901234567"
)


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError('Email yoki telefon raqam kiritilishi shart')

        if email:
            email = self.normalize_email(email).lower()

        user = self.model(email=email, phone_number=phone_number, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

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

    # Login maydonlari
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        validators=[phone_regex]
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        null=True,
        blank=True
    )

    # Shaxsiy ma'lumotlar
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True, verbose_name="Sharif")

    # Tashkilot uchun
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=150, blank=True, null=True, verbose_name="Lavozim")

    # Telegram bot uchun
    chat_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return self.email or self.phone_number or f"User #{self.id}"

    def get_full_name(self):
        if self.user_type == 'organization':
            return self.organization_name or self.email or self.phone_number
        full = f"{self.last_name} {self.first_name} {self.middle_name}".strip()
        return full if full else (self.email or self.phone_number or f"User #{self.id}")
