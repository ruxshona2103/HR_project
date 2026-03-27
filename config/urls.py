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


urlpatterns = [
    path("", RedirectView.as_view(url="/swagger/"), name="home"),
    path("admin/", admin.site.urls),

    # path("api/users/", include("apps.users.urls")),
    path('api/users/', include('apps.users1.urls')),
    path("api/user_profile/", include("apps.user_profile.urls")),
    path("api/vacancies/", include("apps.vacancies.urls")),
    path("api/interviews/", include("apps.interviews.urls")),
    path("api/profile/", include("apps.profile.urls")),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/landing_page/", include("apps.landing_page.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)