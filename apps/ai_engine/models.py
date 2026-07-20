from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class InterviewResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vacancy_name = models.CharField(max_length=255)
    chat_log = models.JSONField() # Barcha savol-javoblar
    score = models.IntegerField(null=True) # 1-100 gacha ball
    feedback = models.TextField(null=True) # AI xulosasi
    created_at = models.DateTimeField(auto_now_add=True)