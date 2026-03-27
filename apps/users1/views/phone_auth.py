from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from apps.users1.models import OTPAttempt, PendingRegistration, OTPCode, User
from apps.users1.serializers import (
    PhoneCandidateRegisterSerializer,
    PhoneOrganizationRegisterSerializer,
    PhoneLoginRequestSerializer,
    OTPVerifySerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken



@extend_schema(tags=["Phone Auth"])
class PhoneCandidateRegisterView(APIView):
    """
    Telefon orqali nomzod ro'yxatdan o'tish — 1-qadam.

    Ma'lumotlar PendingRegistration ga saqlanadi.
    Telegram bot foydalanuvchiga OTP kod yuboradi.
    Keyin /auth/phone/verify-otp/ ga kodni kiriting.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Telefon orqali nomzod ro'yxatdan o'tish",
        request=PhoneCandidateRegisterSerializer,
        responses={
            200: OpenApiResponse(description="Ma'lumotlar saqlandi, bot OTP yuboradi"),
            400: OpenApiResponse(description="Validatsiya xatosi"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={
                    "phone_number": "+998901234567",
                    "first_name": "Ali",
                    "last_name": "Valiyev",
                    "middle_name": "Akbarovich",
                },
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = PhoneCandidateRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone_number']

        # PendingRegistration ga saqlash (bot shu yerdan o'qiydi)
        PendingRegistration.objects.update_or_create(
            phone_number=phone,
            defaults={
                'user_type': 'candidate',
                'first_name': serializer.validated_data.get('first_name', ''),
                'last_name': serializer.validated_data.get('last_name', ''),
                'middle_name': serializer.validated_data.get('middle_name', ''),
            }
        )

        return Response({
            "message": "Ma'lumotlar saqlandi. Telegram bot orqali OTP kod yuboriladi.",
            "phone_number": phone,
            "next_step": "/api/users/auth/phone/verify-otp/",
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["Phone Auth"])
class PhoneOrganizationRegisterView(APIView):
    """
    Telefon orqali tashkilot ro'yxatdan o'tish — 1-qadam.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Telefon orqali tashkilot ro'yxatdan o'tish",
        request=PhoneOrganizationRegisterSerializer,
        responses={
            200: OpenApiResponse(description="Ma'lumotlar saqlandi, bot OTP yuboradi"),
            400: OpenApiResponse(description="Validatsiya xatosi"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={
                    "phone_number": "+998901234567",
                    "first_name": "Vali",
                    "last_name": "Valiyev",
                    "organization_name": "ABC Company",
                    "position": "HR Manager",
                },
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = PhoneOrganizationRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone_number']

        PendingRegistration.objects.update_or_create(
            phone_number=phone,
            defaults={
                'user_type': 'organization',
                'first_name': serializer.validated_data.get('first_name', ''),
                'last_name': serializer.validated_data.get('last_name', ''),
                'middle_name': serializer.validated_data.get('middle_name', ''),
                'organization_name': serializer.validated_data.get('organization_name', ''),
                'position': serializer.validated_data.get('position', ''),
            }
        )

        return Response({
            "message": "Ma'lumotlar saqlandi. Telegram bot orqali OTP kod yuboriladi.",
            "phone_number": phone,
            "next_step": "/api/users/auth/phone/verify-otp/",
        }, status=status.HTTP_200_OK)



@extend_schema(tags=["Phone Auth"])
class PhoneLoginRequestView(APIView):
    """
    Telefon orqali login — 1-qadam.
    Mavjud foydalanuvchi telefon raqamini kiritadi.
    Bot unga OTP kod yuboradi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Telefon orqali login — OTP so'rash",
        request=PhoneLoginRequestSerializer,
        responses={
            200: OpenApiResponse(description="Bot OTP yuboradi"),
            400: OpenApiResponse(description="Telefon raqam topilmadi"),
            429: OpenApiResponse(description="Blokland"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={"phone_number": "+998901234567"},
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = PhoneLoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone_number']

        # Bloklanganligini tekshirish
        attempt, _ = OTPAttempt.objects.get_or_create(phone_number=phone)
        if attempt.is_blocked():
            return Response({
                "error": "Telefon raqam bloklangan. 10 daqiqadan keyin urinib ko'ring."
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Eski ishlatilmagan kodlarni tozalash
        from datetime import timedelta
        from django.utils import timezone
        OTPCode.objects.filter(
            phone_number=phone,
            is_used=False,
            created_at__lt=timezone.now() - timedelta(minutes=5)
        ).delete()


        return Response({
            "message": "Telegram bot orqali OTP kod yuboriladi.",
            "phone_number": phone,
            "next_step": "/api/users/auth/phone/verify-otp/",
        }, status=status.HTTP_200_OK)



@extend_schema(tags=["Phone Auth"])
class OTPVerifyView(APIView):
    """
    OTP kodni tasdiqlash — login VA register uchun bir xil endpoint.

    - User mavjud bo'lsa → LOGIN qilinadi, JWT token qaytadi
    - PendingRegistration bo'lsa → yangi User yaratiladi, JWT token qaytadi
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="OTP kodni tasdiqlash (login + register)",
        request=OTPVerifySerializer,
        responses={
            200: OpenApiResponse(description="Login — JWT token"),
            201: OpenApiResponse(description="Register — yangi user, JWT token"),
            400: OpenApiResponse(description="Kod noto'g'ri"),
            429: OpenApiResponse(description="Blokland"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={"phone_number": "+998901234567", "code": "123456"},
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            # Noto'g'ri kod — urinish qo'shish
            phone = request.data.get('phone_number', '')
            if not phone.startswith('+'):
                phone = '+' + phone
            if phone:
                attempt, _ = OTPAttempt.objects.get_or_create(phone_number=phone)
                if attempt.is_blocked():
                    return Response({
                        "error": "Telefon raqam bloklangan. 10 daqiqadan keyin urinib ko'ring."
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                attempt.add_attempt()
                remaining = max(0, 5 - attempt.attempts)
                errors = serializer.errors.copy()
                if remaining > 0:
                    errors['attempts_left'] = f"{remaining} ta urinish qoldi."
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone_number']
        otp = serializer.validated_data['otp']

        # Bloklanganligini tekshirish
        attempt, _ = OTPAttempt.objects.get_or_create(phone_number=phone)
        if attempt.is_blocked():
            return Response({
                "error": "Telefon raqam bloklangan. 10 daqiqadan keyin urinib ko'ring."
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Kodni ishlatilgan deb belgilash
        otp.is_used = True
        otp.save()

        # Urinishlarni tozalash
        attempt.reset()

        #  LOGIN holati: User allaqachon mavjud
        existing_user = User.objects.filter(phone_number=phone).first()
        if existing_user:
            # chat_id yangilash (agar bot orqali kelgan bo'lsa)
            if not existing_user.chat_id and otp.chat_id:
                existing_user.chat_id = otp.chat_id
                existing_user.save(update_fields=['chat_id'])

            refresh = RefreshToken.for_user(existing_user)
            return Response({
                "message": "Muvaffaqiyatli kirildi.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "user": {
                    "id": existing_user.id,
                    "email": existing_user.email,
                    "phone_number": existing_user.phone_number,
                    "first_name": existing_user.first_name,
                    "last_name": existing_user.last_name,
                    "user_type": existing_user.user_type,
                }
            }, status=status.HTTP_200_OK)

        # REGISTER holati: PendingRegistration dan user yaratish
        try:
            pending = PendingRegistration.objects.get(phone_number=phone)
        except PendingRegistration.DoesNotExist:
            return Response({
                "error": "Ro'yxat ma'lumotlari topilmadi. Qaytadan ro'yxatdan o'ting."
            }, status=status.HTTP_400_BAD_REQUEST)

        if pending.is_expired():
            pending.delete()
            return Response({
                "error": "Ro'yxat muddati tugagan. Qaytadan ro'yxatdan o'ting."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Yangi user yaratish (parolsiz — telefon orqali kiradi)
        user = User(
            phone_number=phone,
            email=None,
            user_type=pending.user_type,
            first_name=pending.first_name,
            last_name=pending.last_name,
            middle_name=pending.middle_name,
            organization_name=pending.organization_name,
            position=pending.position,
            chat_id=otp.chat_id or None,
        )
        user.set_unusable_password()
        user.save()

        # PendingRegistration ni o'chirish
        pending.delete()

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz.",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone_number,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_type": user.user_type,
            }
        }, status=status.HTTP_201_CREATED)
