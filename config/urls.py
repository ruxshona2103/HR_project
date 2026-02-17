from django.contrib import admin
from django.urls import path, include, re_path
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
        contact=openapi.Contact(email=os.getenv("EMAIL")),
        license=openapi.License(name="BSD Licence")
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    generator_class=JWTSchemaGenerator
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/', include('apps.vacancies.urls')),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]