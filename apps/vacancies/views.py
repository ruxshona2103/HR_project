from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from .models import Vacancy
from .serializers import VacancySerializer
from .permissions import IsVacancyOwnerOrReadOnly

@extend_schema(tags=["Vacancies"])
class VacancyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsVacancyOwnerOrReadOnly]
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        company = getattr(self.request.user, 'company_profile', None)
        if not company:
            raise serializers.ValidationError({"company": "Sizda kompaniya profili mavjud emas."})
        serializer.save(company=company)