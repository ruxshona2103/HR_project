from django.contrib import admin
from .models import Category, Vacancy, Resume, Application


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'category', 'city', 'salary_min', 'salary_max', 'is_active', 'created_at']
    list_filter = ['category', 'city', 'is_active']
    search_fields = ['title', 'company']
    list_editable = ['is_active']


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'phone', 'email', 'created_at']
    search_fields = ['full_name', 'email']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['resume', 'vacancy', 'status', 'applied_at']
    list_filter = ['status']
    list_editable = ['status']
    search_fields = ['resume__full_name', 'vacancy__title']