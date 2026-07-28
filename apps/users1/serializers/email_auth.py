from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
import resend
from apps.users1.models import User, EmailVerificationCode
from django.db import transaction, IntegrityError
import re
import dns.resolver




DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com",
    "tempmail.com", "throwaway.email", "yopmail.com", "sharklasers.com",
    "trashmail.com", "dispostable.com", "mailnull.com", "maildrop.cc",
    "fakeinbox.com", "getnada.com", "discard.email", "mytemp.email",
    "tempinbox.com", "tempr.email", "getairmail.com",
}


def validate_real_email(email: str) -> str:
    """Email format va MX record tekshiruvi"""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise serializers.ValidationError("Email formati noto'g'ri.")

    domain = email.split('@')[1].lower()

    if domain in DISPOSABLE_DOMAINS:
        raise serializers.ValidationError(f"'{domain}' — soxta email xizmati. Haqiqiy email kiriting.")

    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        if not mx_records:
            raise serializers.ValidationError(f"'{domain}' email qabul qilmaydi.")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        raise serializers.ValidationError(f"'{domain}' domeni mavjud emas.")
    except Exception:
        pass

    return email.lower()



class EmailLoginSerializer(serializers.Serializer):
    """Email + Parol bilan kirish"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        password = attrs.get('password')

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError({"detail": "Email yoki parol noto'g'ri."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Foydalanuvchi aktiv emas."})

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone_number,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_type": user.user_type,
            }
        }



class EmailCandidateRegisterSerializer(serializers.Serializer):
    """Email orqali nomzod ro'yxatdan o'tish — 1-qadam"""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Parollar mos kelmadi."})

        attrs['email'] = validate_real_email(attrs['email'])

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Bu email allaqachon ro'yxatdan o'tgan."})

        return attrs

    def save(self):
        email = self.validated_data['email']

        # Eski ishlatilmagan kodlarni o'chirish
        EmailVerificationCode.objects.filter(email=email, is_used=False).delete()

        code = EmailVerificationCode.generate_code()

        verification = EmailVerificationCode.objects.create(
            email=email,
            code=code,
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            middle_name=self.validated_data.get('middle_name', ''),
            password=make_password(self.validated_data['password']),
            user_type='candidate',
        )

        # send_mail(
        #     subject='HR Project — Email Tasdiqlash',
        #     message=(
        #         f"Assalomu alaykum!\n\n"
        #         f"Tasdiqlash kodi: {code}\n\n"
        #         f"Kod 5 daqiqa amal qiladi.\n\n"
        #         f"Hurmat bilan,\nHR Project jamoasi"
        #     ),
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[email],
        #     fail_silently=False,
        # )
        resend.api_key = settings.RESEND_API_KEY

        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [email],
            "subject": "HR Project — Email Tasdiqlash",
            "text": (
                f"Assalomu alaykum!\n\n"
                f"Tasdiqlash kodi: {code}\n\n"
                f"Kod 5 daqiqa amal qiladi.\n\n"
                f"Hurmat bilan,\nHR Project jamoasi"
            ),
        })
        return verification


class EmailOrganizationRegisterSerializer(serializers.Serializer):
    """Email orqali tashkilot ro'yxatdan o'tish — 1-qadam"""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    organization_name = serializers.CharField(max_length=255)
    position = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Parollar mos kelmadi."})

        attrs['email'] = validate_real_email(attrs['email'])

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Bu email allaqachon ro'yxatdan o'tgan."})

        return attrs

    def save(self):
        email = self.validated_data['email']

        EmailVerificationCode.objects.filter(email=email, is_used=False).delete()

        code = EmailVerificationCode.generate_code()

        verification = EmailVerificationCode.objects.create(
            email=email,
            code=code,
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            middle_name=self.validated_data.get('middle_name', ''),
            password=make_password(self.validated_data['password']),
            user_type='organization',
            organization_name=self.validated_data['organization_name'],
            position=self.validated_data.get('position', ''),
        )


        # send_mail(
        #     subject='HR Project — Email Tasdiqlash',
        #     message=(
        #         f"Assalomu alaykum!\n\n"
        #         f"Tasdiqlash kodi: {code}\n\n"
        #         f"Kod 5 daqiqa amal qiladi.\n\n"
        #         f"Hurmat bilan,\nHR Project jamoasi"
        #     ),
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[email],
        #     fail_silently=False,
        # )
        resend.api_key = settings.RESEND_API_KEY

        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [email],
            "subject": "HR Project — Email Tasdiqlash",
            "text": (
                f"Assalomu alaykum!\n\n"
                f"Tasdiqlash kodi: {code}\n\n"
                f"Kod 5 daqiqa amal qiladi.\n\n"
                f"Hurmat bilan,\nHR Project jamoasi"
                ),
            })
        return verification



class VerifyEmailSerializer(serializers.Serializer):
    """Email kodni tasdiqlash va User yaratish — 2-qadam"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        email = attrs['email'].lower()
        code = attrs['code']

        try:
            verification = EmailVerificationCode.objects.get(
                email=email,
                code=code,
                is_used=False
            )
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError({"code": "Kod noto'g'ri yoki eskirgan."})

        if verification.is_expired():
            raise serializers.ValidationError({"code": "Kod muddati tugagan. Yana kod so'rang."})

        attrs['verification'] = verification
        return attrs

    def save(self):
        verification = self.validated_data['verification']

        try:
            with transaction.atomic():
                user = User.objects.create(
                    email=verification.email,
                    first_name=verification.first_name,
                    last_name=verification.last_name,
                    middle_name=verification.middle_name,
                    password=verification.password,
                    user_type=verification.user_type,
                    organization_name=verification.organization_name,
                    position=verification.position,
                )
                verification.is_used = True
                verification.save()
        except IntegrityError:
            raise serializers.ValidationError(
                {"email": "Bu email manzil allaqachon ro'yxatdan o'tgan."}
            )

        return user


class ResendEmailCodeSerializer(serializers.Serializer):
    """Email tasdiqlash kodini qayta yuborish"""
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower()
        # Avval ro'yxatdan o'tish boshlangan bo'lishi kerak
        if not EmailVerificationCode.objects.filter(email=value).exists():
            raise serializers.ValidationError("Avval ro'yxatdan o'tishni boshlang.")
        # Allaqachon tasdiqlangan bo'lmasligi kerak
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon tasdiqlangan.")
        return value

    def save(self):
        email = self.validated_data['email']

        # Oxirgi verification ma'lumotlarini olish
        last = EmailVerificationCode.objects.filter(email=email).order_by('-created_at').first()

        # Eski kodlarni o'chirish
        EmailVerificationCode.objects.filter(email=email, is_used=False).delete()

        # Yangi kod
        code = EmailVerificationCode.generate_code()

        verification = EmailVerificationCode.objects.create(
            email=email,
            code=code,
            first_name=last.first_name,
            last_name=last.last_name,
            middle_name=last.middle_name,
            password=last.password,
            user_type=last.user_type,
            organization_name=last.organization_name,
            position=last.position,
        )

        # send_mail(
        #     subject='HR Project — Yangi Tasdiqlash Kodi',
        #     message=(
        #         f"Assalomu alaykum!\n\n"
        #         f"Yangi tasdiqlash kodi: {code}\n\n"
        #         f"Kod 5 daqiqa amal qiladi.\n\n"
        #         f"Hurmat bilan,\nHR Project jamoasi"
        #     ),
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[email],
        #     fail_silently=False,
        # )
        resend.api_key = settings.RESEND_API_KEY

        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [email],
            "subject": "HR Project — Email Tasdiqlash",
            "text": (
                f"Assalomu alaykum!\n\n"
                f"Tasdiqlash kodi: {code}\n\n"
                f"Kod 5 daqiqa amal qiladi.\n\n"
                f"Hurmat bilan,\nHR Project jamoasi"
            ),
        })
        return verification
