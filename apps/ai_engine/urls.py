from django.urls import path
from .views import ResumeCheckAPIView, InterviewStartAPIView

urlpatterns = [

    path('resume-check/', ResumeCheckAPIView.as_view(), name='ai-resume-check'),
    path('start-interview/<int:vacancy_id>/', InterviewStartAPIView.as_view(), name='ai-interview-start'),
]