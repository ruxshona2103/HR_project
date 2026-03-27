from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users1.models import User, OTPCode
from django.utils import timezone
from datetime import timedelta


class PhoneCandidateRegisterSerializer(serializers.Serializer):
    """Telefon orqali nomzod ro'yxatdan o'tish — 1-qadam"""
    phone_number = serializers.CharField(max_length=15)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_phone_number(self, value):
        if not value.startswith('+'):
            value = '+' + value
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan.")
        return value


class PhoneOrganizationRegisterSerializer(serializers.Serializer):
    """Telefon orqali tashkilot ro'yxatdan o'tish — 1-qadam"""
    phone_number = serializers.CharField(max_length=15)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    organization_name = serializers.CharField(max_length=255)
    position = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_phone_number(self, value):
        if not value.startswith('+'):
            value = '+' + value
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan.")
        return value



class PhoneLoginRequestSerializer(serializers.Serializer):
    """Telefon orqali login — 1-qadam: raqamni kiritish"""
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        if not value.startswith('+'):
            value = '+' + value
        if not User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Bu telefon raqam bilan ro'yxatdan o'tilmagan.")
        return value


class OTPVerifySerializer(serializers.Serializer):
    """
    OTP kodni tasdiqlash — login va register uchun bir xil.
    - Agar User mavjud bo'lsa → LOGIN
    - Agar PendingRegistration mavjud bo'lsa → REGISTER
    """
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6, min_length=6)

    def validate_phone_number(self, value):
        if not value.startswith('+'):
            value = '+' + value
        return value

    def validate(self, attrs):
        phone = attrs['phone_number']
        code = attrs['code']

        # Eskirgan kodlarni tozalash
        OTPCode.objects.filter(
            phone_number=phone,
            created_at__lt=timezone.now() - timedelta(minutes=5)
        ).delete()

        # Kodni topish
        try:
            otp = OTPCode.objects.get(
                phone_number=phone,
                code=code,
                is_used=False
            )
        except OTPCode.DoesNotExist:
            raise serializers.ValidationError({"code": "Kod noto'g'ri yoki eskirgan."})

        if otp.is_expired():
            otp.delete()
            raise serializers.ValidationError({"code": "Kod muddati tugagan. Yana so'rang."})

        attrs['otp'] = otp
        return attrs

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def get_user_data(self, user):
        return {
            "id": user.id,
            "email": user.email,
            "phone_number": user.phone_number,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type,
        }
