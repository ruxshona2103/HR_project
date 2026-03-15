from apps.users.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'middle_name', 'chat_id', 'created_at']
        read_only_fields = ['phone_number', 'chat_id', 'created_at']



class AccountUserProfileSerializer(serializers.ModelSerializer):
    """
    Profil ko'rish va tahrirlash (email o'zgartirib bo'lmaydi)
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "created_at",
            "last_login",
        ]
        read_only_fields = ["id", "email", "created_at", "last_login", "full_name"]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def validate_phone_number(self, value):
        if not value:
            return None
        import re
        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if not re.match(r"^\+?[0-9]{7,15}$", cleaned):
            raise serializers.ValidationError("Noto'g'ri telefon raqam formati.")
        # O'zining raqamidan boshqasi uchun unique tekshirish
        qs = User.objects.filter(phone_number=cleaned).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ishlatilmoqda.")
        return cleaned


class ChangePasswordSerializer(serializers.Serializer):
    """Parolni o'zgartirish"""
    old_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        required=True, write_only=True,
        min_length=8,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Yangi parollar mos kelmadi."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
