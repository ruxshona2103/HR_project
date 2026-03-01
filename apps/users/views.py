import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, inline_serializer
from rest_framework import serializers as s
from .models import OTPCode, OTPAttempt, User
from .serializers import VerifyOTPSerializer, UserSerializer
from .throttling import OTPRequestThrottle
from rest_framework_simplejwt.views import TokenRefreshView


class OTPTokenRefreshView(TokenRefreshView):
    @extend_schema(tags=["OTP Auth"], summary="OTP Auth — Token yangilash")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


class BotLinkView(APIView):

    @extend_schema(
        tags=["OTP Auth"],
        summary="Telegram bot linki",
        description="Telegram bot linkini qaytaradi",
        responses={200: inline_serializer("BotLinkResponse", fields={
            "bot_link": s.CharField()
        })}
    )
    def get(self, request):
        bot_username = os.getenv('BOT_USERNAME')
        return Response({"bot_link": f"https://t.me/{bot_username}"})


class VerifyOTPView(APIView):
    throttle_classes = [OTPRequestThrottle]

    @extend_schema(
        tags=["OTP Auth"],
        summary="Sign up & Sign in",
        description="OTP kodni tekshiradi va JWT token qaytaradi",
        request=VerifyOTPSerializer,
        responses={200: OpenApiResponse(description="Muvaffaqiyatli — tokenlar qaytadi")}
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
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            otp = OTPCode.objects.get(phone_number=phone, code=code, is_used=False)
        except OTPCode.DoesNotExist:
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
                'name': user.name,  # ✅ 'nmae' typo ham to'g'irlandi
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):

    @extend_schema(
        tags=["OTP Auth"],
        summary="Logout",
        description="Refresh tokenni blacklistga soladi",
        request=inline_serializer("LogoutRequest", fields={
            "refresh": s.CharField()
        }),
        responses={200: OpenApiResponse(description="Chiqildi")}
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
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Profil"],
        summary="Profil ma'lumotlarini ko'rish",
        responses={200: UserSerializer}
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        tags=["Profil"],
        summary="Profil ma'lumotlarini tahrirlash",
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)