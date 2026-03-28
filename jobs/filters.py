import django_filters
from .models import Vacancy


class VacancyFilter(django_filters.FilterSet):
    """
    Vakansiyalarni filtrlash uchun

    Misol:
      /api/vacancies/?category=1&city=toshkent&salary_min=500&salary_max=2000
    """
    category = django_filters.NumberFilter(
        field_name='category__id',
        label='Soha (ID)'
    )
    city = django_filters.CharFilter(
        field_name='city',
        lookup_expr='iexact',
        label='Shahar'
    )
    salary_min = django_filters.NumberFilter(
        field_name='salary_min',
        lookup_expr='gte',
        label='Minimal maosh (dan)'
    )
    salary_max = django_filters.NumberFilter(
        field_name='salary_max',
        lookup_expr='lte',
        label='Maksimal maosh (gacha)'
    )

    class Meta:
        model = Vacancy
        fields = ['category', 'city', 'salary_min', 'salary_max']