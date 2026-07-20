from django.urls import path
from .views import get_my_profile, ai_resume_check

urlpatterns = [
    path('profile/', get_my_profile, name='candidate-profile'),
    path('ai-check/', ai_resume_check, name='ai-resume-check'),
]