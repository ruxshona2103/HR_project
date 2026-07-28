"""
config/urls.py — Production Ready URL Configuration
"""
from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from apps.users1.views.telegram_connect import (
    TelegramConnectView,
    TelegramDisconnectView,
    TelegramStatusView,
)


def health_check(request):
    db_ok = True
    cache_ok = True

    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False

    try:
        cache.set("health_check_ping", "pong", 5)
        if cache.get("health_check_ping") != "pong":
            cache_ok = False
    except Exception:
        cache_ok = False

    if db_ok and cache_ok:
        return JsonResponse({"status": "ok", "database": "connected", "cache": "connected"}, status=200)
    else:
        return JsonResponse({
            "status": "error",
            "database": "ok" if db_ok else "down",
            "cache": "ok" if cache_ok else "down"
        }, status=503)

urlpatterns = [
    path("", RedirectView.as_view(url="/swagger/"), name="home"),
    path("admin/", admin.site.urls),

    path("api/users/", include("apps.users1.urls")),
    path("api/user_profile/", include("apps.user_profile.urls")),
    path("api/vacancies/", include("apps.vacancies.urls")),
    path("api/profile/", include("apps.profile.urls")),
    path("api/landing_page/", include("apps.landing_page.urls")),
    path("api/resume/", include("apps.resume.urls")),
    path("api/ai_interview/", include("apps.ai_engine.urls")),

    path(
        "api/users/telegram/connect/",
        TelegramConnectView.as_view(),
        name="telegram-connect",
    ),
    path(
        "api/users/telegram/disconnect/",
        TelegramDisconnectView.as_view(),
        name="telegram-disconnect",
    ),
    path(
        "api/users/telegram/status/",
        TelegramStatusView.as_view(),
        name="telegram-status",
    ),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path('api/health/', health_check, name='health-check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)