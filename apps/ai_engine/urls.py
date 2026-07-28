from django.urls import path
from .views import (
    ResumeCheckAPIView,
    InterviewStartAPIView,
    InterviewStatusAPIView,
    InterviewFeedbackAPIView,
)


urlpatterns = [
    path('resume-check/', ResumeCheckAPIView.as_view(), name='ai-resume-check'),
    path('start-interview/<int:vacancy_id>/', InterviewStartAPIView.as_view(), name='ai-interview-start'),
    path('status/<int:vacancy_id>/', InterviewStatusAPIView.as_view(), name='ai-interview-status'),
    path('feedback/<int:result_id>/', InterviewFeedbackAPIView.as_view(), name='ai-interview-feedback'),
]