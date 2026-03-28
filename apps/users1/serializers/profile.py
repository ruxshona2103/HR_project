from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.users1.models import User
import re


class UserProfileSerializer(serializers.ModelSerializer):
    """Profil ko'rish va tahrirlash"""
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'middle_name',
            'full_name',
            'user_type',
            'organization_name',
            'position',
            'created_at',
            'last_login',
        ]
        read_only_fields = ['id', 'email', 'user_type', 'created_at', 'last_login', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def validate_phone_number(self, value):
        if not value:
            return None
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
            raise serializers.ValidationError("Noto'g'ri telefon raqam formati.")
        # O'zidan boshqa userda bu raqam yo'qligini tekshirish
        qs = User.objects.filter(phone_number=cleaned).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ishlatilmoqda.")
        return cleaned


class ChangePasswordSerializer(serializers.Serializer):
    """Parolni o'zgartirish (faqat email orqali ro'yxatdan o'tgan userlar uchun)"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Yangi parollar mos kelmadi."})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class LogoutSerializer(serializers.Serializer):
    """Logout — refresh tokenni blacklist qilish"""
    refresh = serializers.CharField(help_text="Refresh token")
