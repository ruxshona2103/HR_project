from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Ro'yxatdan o'tish:
    - email (majburiy, unique)
    - phone_number (ixtiyoriy, unique)
    - password / password_confirm
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        validators=[validate_password],
        style={"input_type": "password"},
        help_text="Kamida 8 ta belgi",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Parolni qayta kiriting",
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "phone_number": {"required": False},
        }

    def validate_email(self, value):
        return value.lower().strip()

    def validate_phone_number(self, value):
        if not value:
            return value
        # Faqat +, raqamlar va bo'shliq bo'lsin
        import re
        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if not re.match(r"^\+?[0-9]{7,15}$", cleaned):
            raise serializers.ValidationError(
                "Noto'g'ri telefon raqam formati. Masalan: +998901234567"
            )
        if User.objects.filter(phone_number=cleaned).exists():
            raise serializers.ValidationError(
                "Bu telefon raqam allaqachon ro'yxatdan o'tgan."
            )
        return cleaned

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Parollar mos kelmadi."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        # bo'sh string bo'lsa None qilish (unique constraint uchun)
        if not validated_data.get("phone_number"):
            validated_data["phone_number"] = None
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """
    Email + Parol → access + refresh token
    Javobga user ma'lumotlari ham qo'shiladi
    """
    def validate(self, attrs):
        attrs[self.username_field] = attrs.get(self.username_field, "").lower().strip()
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "phone_number": self.user.phone_number,
            "is_staff": self.user.is_staff,
        }
        return data


class UserProfileSerializer(serializers.ModelSerializer):
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
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "email", "date_joined", "last_login", "full_name"]

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
