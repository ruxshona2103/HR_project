from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, serializers
from .models import Vacancy
from .serializers import VacancySerializer
from .permissions import IsVacancyOwnerOrReadOnly


@extend_schema(tags=["Vacancies"])
class VacancyViewSet(viewsets.ModelViewSet):
    """
    - GET (list/retrieve): hammaga ochiq (public).
    - POST: faqat 'organization' turidagi autentifikatsiyadan o'tgan foydalanuvchilarga.
    - PUT/PATCH/DELETE: faqat vakansiya egasi bo'lgan kompaniyaga.

    E'tibor bering: `IsAuthenticated` maxsus qo'shilmagan, chunki u GET
    so'rovlarini ham anonim foydalanuvchilar uchun bloklab qo'yardi.
    Autentifikatsiya va egalik tekshiruvlari to'liq `IsVacancyOwnerOrReadOnly`
    ichida amalga oshiriladi.
    """

    permission_classes = [IsVacancyOwnerOrReadOnly]
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        company = getattr(self.request.user, 'company_profile', None)
        if not company:
            raise serializers.ValidationError({"company": "Sizda kompaniya profili mavjud emas."})
        serializer.save(company=company)