from rest_framework import serializers
from .models import Experience, Education, Skill, Language
from django.contrib.auth.models import User


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['id', 'company', 'position', 'start_date', 'end_date', 'description']

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'institution', 'degree', 'start_date', 'end_date']

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'level']

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'level']

class FullResumeSerializer(serializers.ModelSerializer):
    # Kichik serializatorlarni chaqiramiz
    # many=True -> Chunki tajriba bitta emas, ko'p bo'lishi mumkin
    # read_only=True -> Bu faqat ko'rish uchun, o'zgartirish uchun emas
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', # Foydalanuvchi ma'lumotlari
            'experiences', 'educations', 'skills', 'languages'    # Qo'shimcha jadvallar
        ]