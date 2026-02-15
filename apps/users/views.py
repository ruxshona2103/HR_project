import os
from email.policy import default

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .models import OTPCode, OTPAttempt, User
from .serializers import VerifyOTPSerializer, UserSerializer
from .throttling import OTPRequestThrottle


def get_tokens_for_user(user):
    """Userga tokenlar beradi"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


class BotLinkView(APIView):
    """Botni linkimi qaytaradi"""
    @swagger_auto_schema(
        operation_summary="Telegram bot linki",
        operation_description="Telegram bot linkini qaytaradi",
        responses={200: openapi.Response('Bot link', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'bot_link': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ))}
    )
    def get(self, request):
        bot_username = os.getenv('BOT_USERNAME')
        return Response({"bot_link": f"https://t.me/{bot_username}"})


class VerifyOTPView(APIView):
    """OTP kodni tekshoradi va JWT qaytaradi"""
    throttle_classes = [OTPRequestThrottle]
    @swagger_auto_schema(
        operation_summary="sign up & sign in qilish",
        operation_description="OTP kodni tekshiradi va JWT token qaytaradi",
        request_body=VerifyOTPSerializer,
        responses={200: openapi.Response('Muvaffaqiyatli')}
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']

        attempt, _ = OTPAttempt.objects.get_or_create(phone_number=phone)

        if attempt.is_blocked():
            return Response({'error': "Telefon raqam bloklangan. 10 daqiqadan keyin urinib ko'ring"},
                            status=status.HTTP_429_TOO_MANY_REQUESTS
                            )
        try:
            otp = OTPCode.objects.get(
                phone_number=phone,
                code=code,
                is_used=False
            )
        except OTPCode.DoesNotExist:
            """Agar otp kod xato bo'lsa attempt ga +1 qo'shamiz"""
            attempt.add_attempt()
            remaining = 5 - attempt.attempts
            return Response(
                {"error": f"Kod noto'g'ri. {remaining} ta urinish qoldi"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.is_expired():
            attempt.add_attempt()
            return Response(
                {"error": "Kod muddati tugagan. Qaytadan urinib ko'ring"},
                      status=status.HTTP_400_BAD_REQUEST)

        """agar kod to'g'ri bo'lsa attemptni 0 is_used ni True qilamiz"""
        attempt.reset()
        otp.is_used = True
        otp.save()

        user, created = User.objects.get_or_create(
            phone_number=phone,
            defaults={
                'chat_id': otp.chat_id,
                'name': otp.username or ''
            }
        )

        if not created:
            user.chat_id = otp.chat_id
            user.save()
        tokens = get_tokens_for_user(user)

        return Response({
            'message': "Ro'yxatdan o'tildi" if created else "Muvaffaqiyatli kirildi",
            'tokens': tokens,
            'user': {
                'phone_number': user.phone_number,
                'nmae': user.name,
            }
        },
        status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Chiqib ketish"""
    @swagger_auto_schema(
        operation_summary="logout qilish",
        operation_description="Refresh tokenni blacklistga soladi",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: openapi.Response('Chiqildi')}
    )
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': "Chiqildi"}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {'error': "Token noto'g'ri"},
            status=status.HTTP_400_BAD_REQUEST
            )


class MeView(APIView):
    """Profil ma'lumotlarini ko'rish va tahrirlash """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Profil ma'lumotlarini ko'rish",
        operation_description="Profil ma'lumotlarini ko'rish",
        responses={200: UserSerializer()}
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Profil Ma'lumotlarini tahrirlash",
        operation_description="Profil Ma'lumotlarini tahrirlash",
        request_body=UserSerializer,
        responses={200: UserSerializer()}
    )
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
