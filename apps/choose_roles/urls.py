from django.urls import path
from .views import ChooseRoleView

app_name = 'choose_roles' # App nomini aniq belgilash (Namespace)

urlpatterns = [
    path('choose-role/', ChooseRoleView.as_view(), name='choose-role'),
]