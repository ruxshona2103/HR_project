from django.contrib import admin
<<<<<<< HEAD
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
=======
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

# drf-spectacular (Jahongir)
>>>>>>> main
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
<<<<<<< HEAD
=======

# drf-yasg (Sherik)
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from dotenv import load_dotenv
import os

load_dotenv()


class JWTSchemaGenerator(OpenAPISchemaGenerator):
    def get_security_definitions(self):
        return {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': "Tokenni quyidagi formatda kiriting: 'Bearer <sizning_tokeningiz>'"
            }
        }


schema_view = get_schema_view(
    openapi.Info(
        title="API HR",
        default_version="v1",
        description="HR PROJECTning APIlari",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email=os.getenv("EMAIL", "admin@example.com")),
        license=openapi.License(name="BSD Licence")
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    generator_class=JWTSchemaGenerator
)
>>>>>>> main

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

<<<<<<< HEAD
    # Auth API
    path("api/auth/", include("accounts.urls", namespace="accounts")),

    # Swagger UI  →  http://localhost:8000/api/docs/
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
=======
    # Jahongir: Email auth API
    path("api/auth/", include("apps.accounts.urls", namespace="accounts")),

    # Sherik: Users API
    path("api/users/", include("apps.users.urls")),

    # drf-spectacular Swagger (Jahongir)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # drf-yasg Swagger (Sherik)
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc-yasg/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
>>>>>>> main
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
<<<<<<< HEAD
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
=======
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
>>>>>>> main
