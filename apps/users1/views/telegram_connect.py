"""
apps/users1/views/telegram_connect.py

Telegram bot bilan platformani bog'lash uchun API endpointlar.
"""

from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import logging
logger = logging.getLogger(__name__)

@extend_schema(tags=["Telegram Bot"])
class TelegramConnectView(APIView):
    """
    Bot token orqali Telegram akkauntni platformaga bog'lash.

    Ishlash tartibi:
      1. Bot foydalanuvchiga havola beradi:
             GET /api/users/telegram/connect/?token=<token>&chat_id=<chat_id>
         Bu havola tokenning haqiqiyligini tekshiradi.

      2. Foydalanuvchi «Bog'lash» tugmasini bosganda:
             POST /api/users/telegram/connect/
             { "token": "...", "chat_id": "..." }
         Bu so'rov chat_id ni foydalanuvchi profiliga yozadi.

    Muhim: Foydalanuvchi login qilgan bo'lishi shart (JWT Bearer token).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Tokenni tekshirish (bot havolasidan o'tganda)",
        parameters=[
            OpenApiParameter("token", str, description="Bot tomonidan berilgan bir martalik token"),
            OpenApiParameter("chat_id", str, description="Telegram chat ID"),
        ],
        responses={
            200: OpenApiResponse(description="Token yaroqli — bog'lashga tayyor"),
            400: OpenApiResponse(description="Token muddati o'tgan yoki noto'g'ri"),
            404: OpenApiResponse(description="Token topilmadi"),
        },
    )
    def get(self, request):
        token_str = request.query_params.get("token", "").strip()
        chat_id = request.query_params.get("chat_id", "").strip()

        if not token_str or not chat_id:
            return Response(
                {"error": "token va chat_id parametrlari talab qilinadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Token modelini import qilamiz
        try:
            from apps.users1.models import TelegramLinkToken
            token_obj = TelegramLinkToken.objects.filter(token=token_str).first()
        except Exception as e:
            token_obj = None
            logger.error(f"Telegram akkauntni bog'lashda kutilmagan xatolik: {e}")
            return Response(
                {"error": "Telegramni bog'lash jarayonida xatolik yuz berdi. Qaytadan urinib ko'ring."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not token_obj:
            # Token modeli yo'q holda ham ishlashi uchun: chat_id ni bevosita bog'laymiz
            return Response(
                {
                    "status": "ready",
                    "message": "Bogʻlash uchun POST so'rov yuboring.",
                    "token": token_str,
                    "chat_id": chat_id,
                }
            )

        if not token_obj.is_valid():
            return Response(
                {"error": "Token muddati tugagan yoki allaqachon ishlatilgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        time_left = int((token_obj.expires_at - timezone.now()).total_seconds())
        return Response({
            "status": "valid",
            "message": "Token yaroqli. Bog'lash uchun POST so'rov yuboring.",
            "expires_in_seconds": max(0, time_left),
        })

    @extend_schema(
        summary="Telegram akkauntni bog'lash",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Bot token"},
                    "chat_id": {"type": "string", "description": "Telegram chat ID"},
                },
                "required": ["token", "chat_id"],
            }
        },
        responses={
            200: OpenApiResponse(description="Muvaffaqiyatli bog'landi"),
            400: OpenApiResponse(description="Xato ma'lumot"),
        },
    )
    def post(self, request):
        token_str = request.data.get("token", "").strip()
        chat_id = request.data.get("chat_id", "").strip()

        if not token_str or not chat_id:
            return Response(
                {"error": "token va chat_id talab qilinadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.users1.models import User, TelegramLinkToken
        from django.db import transaction

        try:
            with transaction.atomic():
                token_obj = TelegramLinkToken.objects.filter(token=token_str).first()

                if not token_obj:
                    return Response(
                        {"error": "Yaroqsiz yoki topilmagan token."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if token_obj.is_used or (hasattr(token_obj, 'is_valid') and not token_obj.is_valid()):
                    return Response(
                        {"error": "Token yaroqsiz yoki muddati tugagan."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                User.objects.filter(chat_id=chat_id).exclude(id=request.user.id).update(chat_id=None)

                token_obj.user = request.user
                token_obj.is_used = True
                token_obj.save(update_fields=["user", "is_used"])

                request.user.chat_id = chat_id
                request.user.save(update_fields=["chat_id"])

        except Exception as e:
            logger.error(f"Telegram akkauntni bog'lashda kutilmagan xatolik: {e}", exc_info=True)
            return Response(
                {"error": "Telegramni bog'lash jarayonida xatolik yuz berdi. Qaytadan urinib ko'ring."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "status": "success",
            "message": "Telegram akkauntingiz muvaffaqiyatli bog'landi!",
            "chat_id": chat_id,
        })


@extend_schema(tags=["Telegram Bot"])
class TelegramDisconnectView(APIView):
    """Telegram akkauntni profildan ajratish"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Telegram bog'lanishini uzish",
        responses={200: OpenApiResponse(description="Muvaffaqiyatli ajratildi")},
    )
    def post(self, request):
        request.user.chat_id = None
        request.user.save(update_fields=["chat_id"])
        return Response({"message": "Telegram bog'lanishi uzildi."})


@extend_schema(tags=["Telegram Bot"])
class TelegramStatusView(APIView):
    """Foydalanuvchining Telegram bog'lanish holati"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Telegram holati",
        responses={200: OpenApiResponse(description="Holat ma'lumoti")},
    )
    def get(self, request):
        import os
        bot_username = os.getenv("BOT_USERNAME", "hr_mock_bot")
        is_linked = bool(request.user.chat_id)
        return Response({
            "is_linked": is_linked,
            "chat_id": request.user.chat_id if is_linked else None,
            "bot_url": f"https://t.me/{bot_username}",
            "connect_instructions": (
                "Bog'lash uchun botga /start yozing va "
                "«Platforma bilan bog'lash» tugmasini bosing."
                if not is_linked else
                "Akkauntingiz allaqachon bot bilan bog'langan."
            ),
        })