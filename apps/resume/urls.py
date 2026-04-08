from django.urls import path
from .views import ResumeView, ResumeSectionListView, ResumeSectionDetailView

urlpatterns = [
    path('', ResumeView.as_view(), name='resume'),

    path('sections/<str:section>/',
         ResumeSectionListView.as_view(), name='section-list'),

    path('sections/<str:section>/<int:pk>/',
         ResumeSectionDetailView.as_view(), name='section-detail'),
]


