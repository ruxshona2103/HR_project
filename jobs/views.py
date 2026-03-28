from django.shortcuts import render
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User

from .models import Category, Vacancy, Resume, Application
from .serializers import (
    CategorySerializer,
    VacancyListSerializer,
    VacancyDetailSerializer,
    VacancyCreateSerializer,
    ResumeSerializer,
    ApplicationSerializer,
    UserRegisterSerializer,
)
from .filters import VacancyFilter




class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50



class RegisterView(generics.CreateAPIView):
    """Yangi foydalanuvchi ro'yxatdan o'tkazish"""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]




class CategoryListView(generics.ListAPIView):
    """Barcha sohalar ro'yxati"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]




class VacancyListView(generics.ListAPIView):
    """
    Vakansiyalar ro'yxati — filtrlash va qidirish bilan.

    Filtrlash parametrlari:
      - category   : soha id (masalan: ?category=1)
      - city       : shahar (masalan: ?city=toshkent)
      - salary_min : minimal maosh (masalan: ?salary_min=500)
      - salary_max : maksimal maosh (masalan: ?salary_max=2000)

    Qidirish:
      - search: lavozim yoki kompaniya nomi bo'yicha (?search=python)

    Saralash:
      - ordering: ?ordering=salary_min yoki ?ordering=-created_at
    """
    queryset = Vacancy.objects.filter(is_active=True).select_related('category')
    serializer_class = VacancyListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VacancyFilter
    search_fields = ['title', 'company', 'description']
    ordering_fields = ['salary_min', 'salary_max', 'created_at']
    ordering = ['-created_at']


class VacancyDetailView(generics.RetrieveAPIView):
    """Bitta vakansiya to'liq ma'lumoti"""
    queryset = Vacancy.objects.filter(is_active=True)
    serializer_class = VacancyDetailSerializer
    permission_classes = [AllowAny]


class VacancyCreateView(generics.CreateAPIView):
    """Yangi vakansiya qo'shish (faqat admin)"""
    queryset = Vacancy.objects.all()
    serializer_class = VacancyCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()




class ResumeView(generics.RetrieveUpdateAPIView):
    """
    Foydalanuvchining o'z rezyumesi.
    GET  — ko'rish
    PUT/PATCH — yangilash
    """
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        resume, _ = Resume.objects.get_or_create(
            user=self.request.user,
            defaults={
                'full_name': self.request.user.get_full_name() or self.request.user.username,
                'phone': '',
                'email': self.request.user.email,
                'skills': '',
            }
        )
        return resume




class ApplicationListCreateView(generics.ListCreateAPIView):
    """
    GET  — foydalanuvchining barcha arizalari
    POST — yangi ariza topshirish (vakansiyaga rezyumeni biriktirish)
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        return Application.objects.filter(
            resume__user=self.request.user
        ).select_related('vacancy', 'vacancy__category', 'resume')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ApplicationDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    — bitta ariza ma'lumoti
    DELETE — arizani bekor qilish
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        return Application.objects.filter(resume__user=self.request.user)


class VacancyApplicationsView(generics.ListAPIView):
    """
    Muayyan vakansiyaga kelgan barcha arizalar (admin uchun).
    GET /api/vacancies/<id>/applications/
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        vacancy_id = self.kwargs.get('pk')
        return Application.objects.filter(
            vacancy_id=vacancy_id
        ).select_related('resume', 'vacancy')