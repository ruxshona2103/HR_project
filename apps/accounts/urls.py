from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import EmailTokenRefreshView

app_name = "accounts"

urlpatterns = [
    # ── Autentifikatsiya ──────────────────────────────────
    path("register/",        views.RegisterView.as_view(),      name="register"),
    path("login/",           views.LoginView.as_view(),         name="login"),
    path("logout/",          views.LogoutView.as_view(),        name="logout"),
    path("token/refresh/",   EmailTokenRefreshView.as_view(),  name="token_refresh"),

    # ── Profil ────────────────────────────────────────────
    path("me/",              views.MeView.as_view(),             name="me"),
    path("profile/",         views.ProfileView.as_view(),        name="profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
]
