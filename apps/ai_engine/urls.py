from django.urls import path
from .views import ResumeCheckAPIView, InterviewStartAPIView, get_interview_status, get_ai_feedback


urlpatterns = [
    path('resume-check/', ResumeCheckAPIView.as_view(), name='ai-resume-check'),
    path('start-interview/<int:vacancy_id>/', InterviewStartAPIView.as_view(), name='ai-interview-start'),
    path('status/<int:vacancy_id>/', get_interview_status, name='ai-interview-status'),
    path('feedback/<int:result_id>/', get_ai_feedback, name='ai-interview-feedback'),
]