# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from django.views.generic import RedirectView
# from drf_spectacular.views import (
#     SpectacularAPIView,
#     SpectacularSwaggerView,
#     SpectacularRedocView,
# )
#
# urlpatterns = [
#     path("", RedirectView.as_view(url="/swagger/"), name="home"),
#     path("admin/", admin.site.urls),
#
#     path('api/users/', include('apps.users1.urls')),
#     path("api/user_profile/", include("apps.user_profile.urls")),
#     path("api/vacancies/", include("apps.vacancies.urls")),
#     path("api/profile/", include("apps.profile.urls")),
#     path("api/landing_page/", include("apps.landing_page.urls")),
#     path("api/resume/", include("apps.resume.urls")),
#
#     path("api/telegram", include("config.urls_telegram")),
#
#     path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
#     path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
#     path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
# ]
#
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


"""

O'zgarishlar:
  + /api/users/telegram/connect/    → TelegramConnectView
  + /api/users/telegram/disconnect/ → TelegramDisconnectView
  + /api/users/telegram/status/     → TelegramStatusView

Bu faylni loyihangizning config/urls.py fayli bilan ALMASHTIRING.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
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

urlpatterns = [
    path("", RedirectView.as_view(url="/swagger/"), name="home"),
    path("admin/", admin.site.urls),

    # Mavjud API endpointlar
    path("api/users/", include("apps.users1.urls")),
    path("api/user_profile/", include("apps.user_profile.urls")),
    path("api/vacancies/", include("apps.vacancies.urls")),
    path("api/profile/", include("apps.profile.urls")),
    path("api/landing_page/", include("apps.landing_page.urls")),
    path("api/resume/", include("apps.resume.urls")),

    #  Telegram Bot endpointlari

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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)