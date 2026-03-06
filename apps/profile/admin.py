from django.contrib import admin

from .models import CompanyProfile, AIInterviewQuestion


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "industry", "created_at")
    search_fields = ("name", "user__phone_number")
    list_filter = ("industry",)


@admin.register(AIInterviewQuestion)
class AIInterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "question_type", "difficulty", "is_active", "created_at")
    list_filter = ("question_type", "difficulty", "is_active")
    search_fields = ("text", "company__name")

