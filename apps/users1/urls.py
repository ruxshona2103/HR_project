from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users1.views import (
    PhoneCandidateRegisterView,
    PhoneOrganizationRegisterView,
    PhoneLoginRequestView,
    OTPVerifyView,

    EmailLoginView,
    EmailCandidateRegisterView,
    EmailOrganizationRegisterView,
    VerifyEmailView,
    ResendEmailCodeView,

    MeView,
    ChangePasswordView,
    LogoutView,
    DeleteAccountView,
    BotLinkView,

    TelegramConnectView,
    TelegramDisconnectView,
    TelegramStatusView,
)

app_name = 'users1'

urlpatterns = [

    path('auth/phone/register/candidate/',
         PhoneCandidateRegisterView.as_view(),
         name='phone-candidate-register'),

    path('auth/phone/register/organization/',
         PhoneOrganizationRegisterView.as_view(),
         name='phone-organization-register'),

    path('auth/phone/login/',
         PhoneLoginRequestView.as_view(),
         name='phone-login'),

    path('auth/phone/verify-otp/',
         OTPVerifyView.as_view(),
         name='phone-verify-otp'),

    path('auth/email/login/',
         EmailLoginView.as_view(),
         name='email-login'),

    path('auth/email/register/candidate/',
         EmailCandidateRegisterView.as_view(),
         name='email-candidate-register'),

    path('auth/email/register/organization/',
         EmailOrganizationRegisterView.as_view(),
         name='email-organization-register'),

    path('auth/email/verify/',
         VerifyEmailView.as_view(),
         name='email-verify'),

    path('auth/email/resend-code/',
         ResendEmailCodeView.as_view(),
         name='email-resend-code'),

    path('auth/token/refresh/',
         TokenRefreshView.as_view(),
         name='token-refresh'),

    path('auth/logout/',
         LogoutView.as_view(),
         name='logout'),

    path('me/',
         MeView.as_view(),
         name='me'),

    path('change-password/',
         ChangePasswordView.as_view(),
         name='change-password'),

    path('delete-account/',
         DeleteAccountView.as_view(),
         name='delete-account'),

    path('auth/bot-link/',
         BotLinkView.as_view(),
         name='bot-link'),

    path('telegram/connect/',
         TelegramConnectView.as_view(),
         name='telegram-connect'),

    path('telegram/disconnect/',
         TelegramDisconnectView.as_view(),
         name='telegram-disconnect'),

    path('telegram/status/',
         TelegramStatusView.as_view(),
         name='telegram-status'),
]