from .views import LogoutView, MeView, VerifyOTPView, BotLinkView, ChooseRoleView
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/bot-link/', BotLinkView.as_view(), name='bot-link'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),
    # rol tanlash uchun URL
    path('auth/choose-role/', ChooseRoleView.as_view(), name='choose-role'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
