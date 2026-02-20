from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r'^\+\d{10,15}$',
    message="Telefon raqam to'g'ri formatda bo'lishi kerak. Masalan: +998xxxxxxxxx yoki +7xxxxxxxxxx "
)


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Telefon raqam kiritilishi shart')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    #  foydalanuvchini rollarga bo'lish(talaba, ish beruvchi)
    ROLE_CHOICES = (
        ('candidate', 'Ish qidiruvchi'),
        ('employer', 'Ish beruvchi'),
    )

    phone_number = models.CharField(max_length=13, unique=True, validators=[phone_regex])
    name = models.CharField(max_length=50, blank=True)
    chat_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number


class OTPCode(models.Model):
    """Vaqtinchalik — bot telefon olganda shu modelga yozadi
    Web sayt shu kodni tekshiradi"""
    phone_number = models.CharField(max_length=13, validators=[phone_regex])
    chat_id = models.CharField(max_length=20)
    username = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        """ 60 sekunddan keyin kod eskiradi """
        return (timezone.now() - self.created_at).total_seconds() > 60

    def __str__(self):
        return f"{self.phone_number} - {self.code}"


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
