from rest_framework import viewsets

from apps.user_profile.models import UserProfile
from apps.user_profile.serializers import UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


