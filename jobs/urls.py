from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [


    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    path('categories/', views.CategoryListView.as_view(), name='category-list'),


    path('vacancies/', views.VacancyListView.as_view(), name='vacancy-list'),
    path('vacancies/create/', views.VacancyCreateView.as_view(), name='vacancy-create'),
    path('vacancies/<int:pk>/', views.VacancyDetailView.as_view(), name='vacancy-detail'),
    path('vacancies/<int:pk>/applications/', views.VacancyApplicationsView.as_view(), name='vacancy-applications'),


    path('resume/', views.ResumeView.as_view(), name='resume'),


    path('applications/', views.ApplicationListCreateView.as_view(), name='application-list'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
]