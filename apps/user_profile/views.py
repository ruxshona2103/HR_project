from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.user_profile.models import UserProfile
from apps.user_profile.serializers import UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


