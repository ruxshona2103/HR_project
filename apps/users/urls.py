from rest_framework.routers import DefaultRouter

from .views import LogoutView, MeView, VerifyOTPView, BotLinkView, CandidateProfileViewSet, UserProfileViewSet
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'userprofile', UserProfileViewSet)
router.register(r'candidateprofile', CandidateProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),

    path('auth/bot-link/', BotLinkView.as_view(), name='bot-link'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
