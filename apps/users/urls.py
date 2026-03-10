from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views import (
    CandidateRegisterView,
    OrganizationRegisterView,
    LoginView,
    LogoutView,
    VerifyOTPView,
    MeView,
    ChangePasswordView,
    BotLinkView,
    DeleteAccountView,
)

app_name = 'users'

urlpatterns = [
    # Auth
    path('auth/register/candidate/', CandidateRegisterView.as_view(), name='register-candidate'),
    path('auth/register/organization/', OrganizationRegisterView.as_view(), name='register-organization'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/bot_link/', BotLinkView.as_view(), name='Bot-link'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),

    # OTP
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),

    # Profile
    path('me/', MeView.as_view(), name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]