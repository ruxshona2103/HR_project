from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.user_profile.views import UserProfileViewSet

router = DefaultRouter()
router.register(r'user_profile', UserProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

