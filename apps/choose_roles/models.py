from django.db import models
from django.conf import settings


class UserRole(models.TextChoices):
    """
    Tizimdagi foydalanuvchi rollari ro'yxati.
    TextChoices ishlatilishi ma'lumotlar bazasida qat'iy va xavfsiz saqlashni ta'minlaydi.
    """
    CANDIDATE = 'candidate', 'Candidate'
    EMPLOYER = 'employer', 'Employer'


class UserProfile(models.Model):
    """
    Asosiy User modeliga tegmagan holda, unga qo'shimcha 'role' maydonini
    ulash uchun ishlatiladigan profil modeli.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=15,
        choices=UserRole.choices,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"
