from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.user_profile.models import UserProfile
from apps.user_profile.permissions import IsProfileOwner
from apps.user_profile.serializers import UserProfileSerializer1


@extend_schema(tags=["User Profile"])
class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProfileOwner]
    serializer_class = UserProfileSerializer1

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return UserProfile.objects.none()
        return UserProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if UserProfile.objects.filter(user=self.request.user).exists():
            raise ValidationError({"detail": "Sizda allaqachon profil mavjud."})
        serializer.save(user=self.request.user)


