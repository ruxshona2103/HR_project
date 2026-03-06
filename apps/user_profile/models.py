from django.db import models


class UserProfile(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    phone_number = models.CharField(max_length=15)
    university_name = models.CharField(max_length=255, null=True, blank=True)
    degree = models.CharField(max_length=100, blank=True, null=True)
    course = models.PositiveSmallIntegerField(blank=True, null=True)
    field_of_study = models.CharField(max_length=255, null=True, blank=True)
    start_year = models.PositiveIntegerField(blank=True, null=True)
    end_year = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"