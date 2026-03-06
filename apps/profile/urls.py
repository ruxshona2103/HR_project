from rest_framework.routers import DefaultRouter

from .views import (
    CompanyProfileViewSet,
    CompanyVacancyViewSet,
    AIInterviewQuestionViewSet,
)

router = DefaultRouter()
router.register(r"company-profile", CompanyProfileViewSet, basename="company-profile")
router.register(r"company-vacancies", CompanyVacancyViewSet, basename="company-vacancy")
router.register(r"ai-questions", AIInterviewQuestionViewSet, basename="ai-questions")

urlpatterns = router.urls

