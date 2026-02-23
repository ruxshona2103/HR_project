from rest_framework import serializers
from .models import UserRole

class RoleSelectionSerializer(serializers.Serializer):
    """
    Foydalanuvchi tanlagan rolni tekshirish uchun serializer.
    Faqat UserRole.choices ichida bor bo'lgan qiymatlarni qabul qiladi.
    """
    role = serializers.ChoiceField(choices=UserRole.choices)