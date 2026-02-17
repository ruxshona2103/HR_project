from django import forms
from django.contrib.auth import authenticate
from rest_framework.fields import CharField


class LoginForm(forms.Form):
    email = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=20)
