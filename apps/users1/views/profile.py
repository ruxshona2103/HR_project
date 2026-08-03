from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
import os

from apps.users1.serializers import (
    UserProfileSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
)


@extend_schema(tags=["Profile"])
class MeView(APIView):
    """Profil ko'rish va tahrirlash"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Profilni ko'rish",
        responses={200: UserProfileSerializer},
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Profilni tahrirlash",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        examples=[
            OpenApiExample(
                "Misol",
                value={"first_name": "Yangi Ism", "last_name": "Yangi Familya", "middle_name": "Yangi familiya"},
                request_only=True,
            )
        ]
    )
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Profile"])
class ChangePasswordView(APIView):
    """Parolni o'zgartirish (faqat email orqali ro'yxatdan o'tganlar uchun)"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Parolni o'zgartirish",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Parol o'zgartirildi"),
            400: OpenApiResponse(description="Xato"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={
                    "old_password": "OldPass123!",
                    "new_password": "NewPass456!",
                    "new_password_confirm": "NewPass456!",
                },
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Parol muvaffaqiyatli o'zgartirildi."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Auth"])
class LogoutView(APIView):
    """Logout — refresh tokenni blacklist qiladi"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout",
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description="Muvaffaqiyatli chiqildi"),
            400: OpenApiResponse(description="Token xato"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={"refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                request_only=True,
            )
        ]
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token kiritilmadi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Muvaffaqiyatli chiqildi."})
        except TokenError:
            return Response(
                {"error": "Yaroqsiz yoki eskirgan refresh token."},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=["Auth"])
class DeleteAccountView(APIView):
    """Accountni butunlay o'chirish"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Accountni o'chirish",
        description="Account butunlay o'chiriladi. Bu amalni qaytarib bo'lmaydi!",
        responses={
            204: OpenApiResponse(description="Account o'chirildi"),
        }
    )
    def delete(self, request):
        request.user.delete()
        return Response(
            {"message": "Account butunlay o'chirildi."},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(tags=["Auth"])
class BotLinkView(APIView):
    """Telegram bot linkini olish"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Telegram bot linki",
        responses={200: OpenApiResponse(description="Bot link")},
    )
    def get(self, request):
        bot_username = os.getenv('BOT_USERNAME', '')
        return Response({"bot_link": f"https://t.me/{bot_username}"})