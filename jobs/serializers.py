from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Vacancy, Resume, Application


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class VacancyListSerializer(serializers.ModelSerializer):
    """Ro'yxat uchun (qisqa ma'lumot)"""
    category = CategorySerializer(read_only=True)
    salary_range = serializers.ReadOnlyField()
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = [
            'id', 'title', 'company', 'category',
            'city', 'salary_min', 'salary_max', 'salary_range',
            'is_active', 'created_at', 'applications_count'
        ]

    def get_applications_count(self, obj):
        return obj.applications.count()


class VacancyDetailSerializer(serializers.ModelSerializer):
    """To'liq ma'lumot"""
    category = CategorySerializer(read_only=True)
    salary_range = serializers.ReadOnlyField()

    class Meta:
        model = Vacancy
        fields = [
            'id', 'title', 'company', 'category',
            'city', 'salary_min', 'salary_max', 'salary_range',
            'description', 'requirements',
            'is_active', 'created_at', 'updated_at'
        ]


class VacancyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = [
            'title', 'company', 'category',
            'city', 'salary_min', 'salary_max',
            'description', 'requirements', 'is_active'
        ]

    def validate(self, data):
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError(
                "Minimal maosh maksimaldan katta bo'lishi mumkin emas."
            )
        return data


class ResumeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Resume
        fields = [
            'id', 'user', 'full_name', 'phone', 'email',
            'skills', 'experience', 'education',
            'resume_file', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']


class ApplicationSerializer(serializers.ModelSerializer):
    vacancy = VacancyListSerializer(read_only=True)
    vacancy_id = serializers.PrimaryKeyRelatedField(
        queryset=Vacancy.objects.filter(is_active=True),
        write_only=True,
        source='vacancy'
    )
    resume = ResumeSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = Application
        fields = [
            'id', 'vacancy', 'vacancy_id', 'resume',
            'cover_letter', 'status', 'status_display', 'applied_at'
        ]
        read_only_fields = ['resume', 'status', 'applied_at']

    def validate(self, data):
        request = self.context.get('request')
        if not hasattr(request.user, 'resume'):
            raise serializers.ValidationError(
                "Ariza topshirish uchun avval rezyume yarating."
            )
        resume = request.user.resume
        vacancy = data.get('vacancy')
        if Application.objects.filter(vacancy=vacancy, resume=resume).exists():
            raise serializers.ValidationError(
                "Siz bu vakansiyaga allaqachon ariza topshirgansiz."
            )
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['resume'] = request.user.resume
        return super().create(validated_data)


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Parollar mos kelmadi.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user