# apps/users/views/email_auth.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.serializers.email_auth import (
    EmailRegisterRequestSerializer,
    VerifyEmailSerializer,
    ResendCodeSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiResponse


class EmailRegisterRequestView(APIView):
    """
    Step 1: Email kiritish va tasdiqlash kodini yuborish

    Email ga 6 raqamli kod yuboriladi (5 daqiqa amal qiladi)
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailRegisterRequestSerializer,
        responses={
            200: OpenApiResponse(description="Kod emailga yuborildi"),
            400: OpenApiResponse(description="Validatsiya xatosi")
        },
        tags=['Email Authentication']
    )
    def post(self, request):
        serializer = EmailRegisterRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Tasdiqlash kodi emailingizga yuborildi. Kodni kiriting.",
                "email": serializer.validated_data['email']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    Step 2: Kodni tekshirish va ro'yxatdan o'tkazish

    To'g'ri kod kiritilsa user yaratiladi va JWT token beriladi
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={
            201: OpenApiResponse(description="Muvaffaqiyatli ro'yxatdan o'tdingiz"),
            400: OpenApiResponse(description="Kod noto'g'ri yoki eskirgan")
        },
        tags=['Email Authentication']
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # JWT token yaratish
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz!",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "user_type": user.user_type
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendCodeView(APIView):
    """
    Kodni qayta yuborish

    Agar kod kelmagan yoki eskirgan bo'lsa yangi kod yuboriladi
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResendCodeSerializer,
        responses={
            200: OpenApiResponse(description="Yangi kod yuborildi"),
            400: OpenApiResponse(description="Email topilmadi")
        },
        tags=['Email Authentication']
    )
    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Yangi tasdiqlash kodi emailingizga yuborildi.",
                "email": serializer.validated_data['email']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)