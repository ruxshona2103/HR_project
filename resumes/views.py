from rest_framework import viewsets, permissions
from .models import Experience, Education, Skill, Language
from .serializers import ExperienceSerializer, EducationSerializer, SkillSerializer, LanguageSerializer

# Barcha ViewSetlar uchun umumiy qulaylik (Mixin) - kodni takrorlamaslik uchun
class BaseResumeViewSet(viewsets.ModelViewSet):
    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Endi har birini alohida yozamiz
class ExperienceViewSet(BaseResumeViewSet):
    serializer_class = ExperienceSerializer
    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user)

class EducationViewSet(BaseResumeViewSet):
    serializer_class = EducationSerializer
    def get_queryset(self):
        return Education.objects.filter(user=self.request.user)

class SkillViewSet(BaseResumeViewSet):
    serializer_class = SkillSerializer
    def get_queryset(self):
        return Skill.objects.filter(user=self.request.user)

class LanguageViewSet(BaseResumeViewSet):
    serializer_class = LanguageSerializer
    def get_queryset(self):
        return Language.objects.filter(user=self.request.user)