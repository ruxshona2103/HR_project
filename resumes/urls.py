from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExperienceViewSet, EducationViewSet, SkillViewSet, LanguageViewSet

router = DefaultRouter()
router.register(r'experience', ExperienceViewSet, basename='experience')
router.register(r'education', EducationViewSet, basename='education')
router.register(r'skills', SkillViewSet, basename='skills')
router.register(r'languages', LanguageViewSet, basename='languages')

urlpatterns = [
    path('', include(router.urls)),
]