from django.db import models

class Vacancy(models.Model):
    TYPE_CHOICES = [
        ('system', 'System'),
        ('national', 'National'),
        ('international', 'International'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    required_skills = models.TextField()
    min_experience = models.IntegerField()

    def __str__(self):
        return self.title

class Candidate(models.Model):
    name = models.CharField(max_length=100)
    skills = models.TextField()
    experience = models.IntegerField()