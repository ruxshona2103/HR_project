from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    # ── Autentifikatsiya ──────────────────────────────────
    path("register/",        views.RegisterView.as_view(),      name="register"),
    path("login/",           views.LoginView.as_view(),          name="login"),
    path("logout/",          views.LogoutView.as_view(),         name="logout"),
    path("token/refresh/",   TokenRefreshView.as_view(),         name="token_refresh"),

    # ── Profil ────────────────────────────────────────────
    path("me/",              views.MeView.as_view(),             name="me"),
    path("profile/",         views.ProfileView.as_view(),        name="profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
]
