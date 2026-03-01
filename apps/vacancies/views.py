from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from .models import Vacancy
from .serializers import VacancySerializer


@extend_schema(tags=["Vacancies"])
class VacancyViewSet(viewsets.ModelViewSet):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    def get_serializer_context(self):
        return {'request': self.request}