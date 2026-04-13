from django.db import models

class CandidateProfile(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    specialty = models.CharField(max_length=255)
    skills = models.JSONField(default=list)  # Ko'nikmalar ro'yxati
    experience = models.TextField()
    about_me = models.TextField()

    def str(self):
        return self.full_name