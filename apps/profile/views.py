from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.vacancies.models import Vacancy
from apps.vacancies.serializers import VacancySerializer
from .models import CompanyProfile, AIInterviewQuestion
from .serializers import CompanyProfileSerializer, AIInterviewQuestionSerializer


@extend_schema(tags=["Company Profile"])
class CompanyProfileViewSet(viewsets.ModelViewSet):
    """
    Tashkilot (kompaniya) profili uchun API.

    - Kompaniya haqida qisqacha ma'lumotni ko'rish va tahrirlash
    - Vakansiyalar statistikasi (umumiy, ochiq, yopilgan)
    """

    queryset = CompanyProfile.objects.select_related("user").all()
    serializer_class = CompanyProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CompanyProfile.objects.none()
        return CompanyProfile.objects.filter(user=user)

    @action(detail=False, methods=["get", "put", "patch"], url_path="me")
    def me(self, request):
        """
        Joriy tizimga kirgan foydalanuvchining kompaniya profilini
        ko'rish va tahrirlash uchun endpoint.
        """
        profile, _ = CompanyProfile.objects.get_or_create(user=request.user)

        if request.method in ("PUT", "PATCH"):
            serializer = self.get_serializer(
                profile,
                data=request.data,
                partial=request.method == "PATCH",
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = self.get_serializer(profile)
        return Response(serializer.data)


@extend_schema(tags=["Company Vacancies"])
class CompanyVacancyViewSet(viewsets.ModelViewSet):
    """
    Tashkilotga tegishli vakansiyalar uchun panel.

    - Kompaniya yuklagan vakansiyalar ro'yxati
    - Yangi vakansiya yaratish
    """

    serializer_class = VacancySerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Vacancy.objects.none()

        try:
            company = user.company_profile
        except CompanyProfile.DoesNotExist:
            return Vacancy.objects.none()

        return Vacancy.objects.filter(company=company)

    def perform_create(self, serializer):
        company = self.request.user.company_profile
        serializer.save(company=company)


@extend_schema(tags=["AI Interview Questions"])
class AIInterviewQuestionViewSet(viewsets.ModelViewSet):
    """
    AI interview uchun savollarni boshqarish:

    - Savollar qo'shish
    - Ro'yxatini ko'rish
    - Tahrirlash va o'chirish
    """

    serializer_class = AIInterviewQuestionSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return AIInterviewQuestion.objects.none()

        try:
            company = user.company_profile
        except CompanyProfile.DoesNotExist:
            return AIInterviewQuestion.objects.none()

        return AIInterviewQuestion.objects.filter(company=company)

    def perform_create(self, serializer):
        company = self.request.user.company_profile
        serializer.save(company=company)

