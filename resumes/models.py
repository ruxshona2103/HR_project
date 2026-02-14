from django.db import models
from django.conf import settings

# ISH TAJRIBASI bloki
class Experience(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.position} at {self.company}"

# TA'LIM
class Education(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=255)  # OTM nomi
    degree = models.CharField(max_length=255)  # Yo'nalish/Mutaxassislik
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.degree} at {self.institution}"


# KO'NIKMALAR
class Skill(models.Model):
    LEVEL_CHOICES = [
        ('Junior', 'Boshlang\'ich'),
        ('Middle', 'O\'rta'),
        ('Senior', 'Yuqori'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)

    def __str__(self):
        return self.name

# TILLAR
class Language(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1 - Boshlang\'ich'),
        ('A2', 'A2 - Elementar'),
        ('B1', 'B1 - O\'rta'),
        ('B2', 'B2 - Yuqori o\'rta'),
        ('C1', 'C1 - Mukammal'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)

    def __str__(self):
        return f"{self.name} - {self.level}"