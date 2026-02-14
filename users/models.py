from django.db import models

class User(models.Model):
    first_name = models.CharField(max_length=50, null=False)
    last_name = models.CharField(max_length=50, null=False)
    age = models.IntegerField(null=False)
    email = models.EmailField(null=False)
    phone_number = models.IntegerField(null=False)


    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(null=False, blank=True)
    linkedin_url = models.URLField(null=False, blank=True)
    github_url = models.URLField(null=False, blank=True)
    portfolio_url = models.URLField(null=False, blank=True)
    experience_years = models.IntegerField(default=0)
    languages = models.JSONField(default=list, blank=True)
    education = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.get_full_name()}'


class HRManagerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.CharField(max_length=200, blank=True)
    position_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company}"



