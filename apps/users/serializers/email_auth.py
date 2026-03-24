# apps/users/serializers/email_auth.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.users.models import User, EmailVerificationCode
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
import re
import dns.resolver

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com",
    "tempmail.com", "throwaway.email", "yopmail.com", "sharklasers.com",
    "guerrillamailblock.com", "grr.la", "guerrillamail.info", "spam4.me",
    "trashmail.com", "dispostable.com", "mailnull.com", "maildrop.cc",
    "fakeinbox.com", "getnada.com", "discard.email", "spamgourmet.com",
    "mytemp.email", "tempinbox.com", "tempr.email", "throwam.com",
    "getairmail.com", "filzmail.com", "emkei.cz",
}


def validate_real_email(email: str) -> str:
    """Email validatsiya + MX record tekshiruvi"""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise serializers.ValidationError("Email formati noto'g'ri.")

    domain = email.split('@')[1].lower()

    if domain in DISPOSABLE_DOMAINS:
        raise serializers.ValidationError(
            f"'{domain}' soxta email xizmati. Haqiqiy email kiriting."
        )

    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        if not mx_records:
            raise serializers.ValidationError(
                f"'{domain}' email qabul qilmaydi."
            )
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        raise serializers.ValidationError(
            f"'{domain}' domeni mavjud emas."
        )
    except Exception:
        pass

    return email.lower()


class EmailRegisterRequestSerializer(serializers.Serializer):
    """Step 1: Email yuborish uchun"""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['candidate', 'organization'])

    # Organization uchun
    organization_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    position = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Parollar mos kelmadi"})

        # Email validatsiya
        attrs['email'] = validate_real_email(attrs['email'])

        # Email allaqachon ro'yxatdan o'tganmi
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError(
                {"email": "Bu email allaqachon ro'yxatdan o'tgan."}
            )

        return attrs

    def save(self):
        """Verification code yaratish va email yuborish"""
        # Eski kodlarni o'chirish
        EmailVerificationCode.objects.filter(
            email=self.validated_data['email'],
            is_used=False
        ).delete()

        # Yangi kod yaratish
        code = EmailVerificationCode.generate_code()

        verification = EmailVerificationCode.objects.create(
            email=self.validated_data['email'],
            code=code,
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            middle_name=self.validated_data.get('middle_name', ''),
            password=make_password(self.validated_data['password']),
            user_type=self.validated_data['user_type'],
            organization_name=self.validated_data.get('organization_name'),
            position=self.validated_data.get('position'),
        )

        # Email yuborish
        send_mail(
            subject='HR Project - Email Tasdiqlash',
            message=f'Assalomu alaykum!\n\nTasdiqlash kodi: {code}\n\nKod 5 daqiqa amal qiladi.\n\nHurmat bilan,\nHR Project jamoasi',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.validated_data['email']],
            fail_silently=False,
        )

        return verification


class VerifyEmailSerializer(serializers.Serializer):
    """Step 2: Kodni tekshirish va user yaratish"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            verification = EmailVerificationCode.objects.get(
                email=attrs['email'],
                code=attrs['code'],
                is_used=False
            )
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError({"code": "Kod noto'g'ri yoki eskirgan."})

        if verification.is_expired():
            raise serializers.ValidationError({"code": "Kod muddati tugagan. Yana kod so'rang."})

        attrs['verification'] = verification
        return attrs

    def save(self):
        """User yaratish"""
        verification = self.validated_data['verification']

        user = User.objects.create(
            email=verification.email,
            first_name=verification.first_name,
            last_name=verification.last_name,
            middle_name=verification.middle_name,
            password=verification.password,  # allaqachon hashed
            user_type=verification.user_type,
            organization_name=verification.organization_name,
            position=verification.position,
        )

        # Kodni ishlatilgan deb belgilash
        verification.is_used = True
        verification.save()

        return user


class ResendCodeSerializer(serializers.Serializer):
    """Kodni qayta yuborish"""
    email = serializers.EmailField()

    def validate_email(self, value):
        # Oxirgi verification ma'lumotlarini tekshirish
        last_verification = EmailVerificationCode.objects.filter(
            email=value
        ).order_by('-created_at').first()

        if not last_verification:
            raise serializers.ValidationError(
                "Avval ro'yxatdan o'tishni boshlang."
            )

        return value

    def save(self):
        # Eski kodlarni o'chirish
        EmailVerificationCode.objects.filter(
            email=self.validated_data['email'],
            is_used=False
        ).delete()

        # Yangi kod
        code = EmailVerificationCode.generate_code()

        # Oxirgi verification ma'lumotlarini olish
        last_verification = EmailVerificationCode.objects.filter(
            email=self.validated_data['email']
        ).order_by('-created_at').first()

        # Yangi kod yaratish
        verification = EmailVerificationCode.objects.create(
            email=last_verification.email,
            code=code,
            first_name=last_verification.first_name,
            last_name=last_verification.last_name,
            middle_name=last_verification.middle_name,
            password=last_verification.password,
            user_type=last_verification.user_type,
            organization_name=last_verification.organization_name,
            position=last_verification.position,
        )

        # Email yuborish
        send_mail(
            subject='HR Project - Yangi Tasdiqlash Kodi',
            message=f'Assalomu alaykum!\n\nYangi tasdiqlash kodi: {code}\n\nKod 5 daqiqa amal qiladi.\n\nHurmat bilan,\nHR Project jamoasi',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.validated_data['email']],
            fail_silently=False,
        )

        return verification