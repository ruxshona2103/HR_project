from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.vacancies.models import Vacancy
from apps.vacancies.serializers import VacancySerializer
from .models import CompanyProfile, AIInterviewQuestion
from .serializers import CompanyProfileSerializer, AIInterviewQuestionSerializer


@extend_schema(tags=["Company Profile"])
class CompanyProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyProfileSerializer
    queryset = CompanyProfile.objects.all()

    def get_queryset(self):
        # Faqat o'zining profilini ko'rsin
        return CompanyProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # STANDART POST SO'ROVI UCHUN: user_id ni biriktiramiz
        if CompanyProfile.objects.filter(user=self.request.user).exists():
            raise ValidationError({"detail": "Sizda allaqachon profil mavjud."})
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get", "put", "patch"], url_path="me")
    def me(self, request):
        # Bu qism to'g'ri, get_or_create user_id ni avtomatik qo'shadi
        profile, _ = CompanyProfile.objects.get_or_create(user=request.user)
        if request.method in ("PUT", "PATCH"):
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


@extend_schema(tags=["Company Vacancies"])
class CompanyVacancyViewSet(viewsets.ModelViewSet):
    serializer_class = VacancySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Userning kompaniyasiga tegishli vakansiyalarni olish
        return Vacancy.objects.filter(company__user=self.request.user)

    def perform_create(self, serializer):
        # Vakansiyani userning kompaniyasiga bog'laymiz
        try:
            company = self.request.user.company_profile
            serializer.save(company=company)
        except CompanyProfile.DoesNotExist:
            raise ValidationError({"detail": "Avval kompaniya profili yarating."})


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

