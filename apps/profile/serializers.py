from rest_framework import serializers

from apps.vacancies.models import Vacancy
from .models import CompanyProfile, AIInterviewQuestion


class CompanyProfileSerializer(serializers.ModelSerializer):
    vacancies_total = serializers.SerializerMethodField()
    vacancies_open = serializers.SerializerMethodField()
    vacancies_closed = serializers.SerializerMethodField()

    class Meta:
        model = CompanyProfile
        fields = [
            "id",
            "name",
            "short_description",
            "website",
            "location",
            "industry",
            "vacancies_total",
            "vacancies_open",
            "vacancies_closed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "vacancies_total",
            "vacancies_open",
            "vacancies_closed",
            "created_at",
            "updated_at",
        ]

    def _company_vacancies(self, obj):
        return Vacancy.objects.filter(company=obj)

    def get_vacancies_total(self, obj) -> int:
        return self._company_vacancies(obj).count()

    def get_vacancies_open(self, obj) -> int:
        from apps.vacancies.models import Vacancy as VacancyModel

        return self._company_vacancies(obj).filter(
            status=VacancyModel.Status.OPEN
        ).count()

    def get_vacancies_closed(self, obj) -> int:
        from apps.vacancies.models import Vacancy as VacancyModel

        return self._company_vacancies(obj).filter(
            status=VacancyModel.Status.CLOSED
        ).count()


class AIInterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInterviewQuestion
        fields = [
            "id",
            "text",
            "question_type",
            "difficulty",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

