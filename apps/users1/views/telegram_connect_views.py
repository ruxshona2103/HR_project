"""
apps/users1/views/telegram_connect.py

Platformadan Telegram botga bog'lash uchun API endpoint.
Bot havolasida: /telegram/connect/?token=<token>&chat_id=<chat_id>
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

import secrets
from datetime import timedelta


@extend_schema(tags=["Telegram Bot"])
class TelegramConnectView(APIView):
    """
    Foydalanuvchi profilidagi «Telegramni ulash» sahifasi.
    Bot tomonidan berilgan token va chat_id orqali akkauntni bog'laydi.

    GET  → Token tekshirish (valid/expired)
    POST → Tokenni ishlatish (chat_id ni akkauntga yozish)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Telegram tokenni tekshirish",
        parameters=[
            OpenApiParameter("token", str, description="Bot tomonidan berilgan bir martalik token"),
            OpenApiParameter("chat_id", str, description="Telegram chat ID"),
        ],
        responses={
            200: OpenApiResponse(description="Token yaroqli"),
            400: OpenApiResponse(description="Token muddati o'tgan yoki noto'g'ri"),
        }
    )
    def get(self, request):
        token_str = request.query_params.get("token")
        chat_id = request.query_params.get("chat_id")

        if not token_str or not chat_id:
            return Response(
                {"error": "token va chat_id parametrlari talab qilinadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.users1.models import TelegramLinkToken

        token_obj = TelegramLinkToken.objects.filter(token=token_str).first()

        if not token_obj:
            return Response(
                {"error": "Token topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not token_obj.is_valid():
            return Response(
                {"error": "Token muddati tugagan yoki allaqachon ishlatilgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "status": "valid",
            "message": "Token yaroqli. Bog'lash uchun POST so'rov yuboring.",
            "expires_in_seconds": max(
                0, int((token_obj.expires_at - timezone.now()).total_seconds())
            ),
        })

    @extend_schema(
        summary="Telegram akkauntni bog'lash",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "chat_id": {"type": "string"},
                },
                "required": ["token", "chat_id"],
            }
        },
        responses={
            200: OpenApiResponse(description="Muvaffaqiyatli bog'landi"),
            400: OpenApiResponse(description="Xato"),
        }
    )
    def post(self, request):
        token_str = request.data.get("token")
        chat_id = request.data.get("chat_id")

        if not token_str or not chat_id:
            return Response(
                {"error": "token va chat_id talab qilinadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.users1.models import TelegramLinkToken, User

        # Boshqa foydalanuvchida bu chat_id bor bo'lsa, tozalash
        User.objects.filter(chat_id=chat_id).exclude(id=request.user.id).update(chat_id=None)

        token_obj = TelegramLinkToken.objects.filter(token=token_str).first()

        if not token_obj or not token_obj.is_valid():
            return Response(
                {"error": "Token yaroqsiz yoki muddati tugagan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Token va chat_id ni biriktirish
        token_obj.user = request.user
        token_obj.consume(chat_id)

        return Response({
            "status": "success",
            "message": "Telegram akkauntingiz muvaffaqiyatli bog'landi!",
            "chat_id": chat_id,
        })


@extend_schema(tags=["Telegram Bot"])
class TelegramDisconnectView(APIView):
    """Telegram akkauntni ajratish"""
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
        summary="Telegram bog'lanish holatini ko'rish",
        responses={200: OpenApiResponse(description="Holat")},
    )
    def get(self, request):
        import os
        bot_username = os.getenv("BOT_USERNAME_2", "hr_mock_bot")
        is_linked = bool(request.user.chat_id)

        return Response({
            "is_linked": is_linked,
            "chat_id": request.user.chat_id if is_linked else None,
            "bot_url": f"https://t.me/{bot_username}",
        })


@extend_schema(tags=["Telegram Bot"])
class SendVacancyNotificationView(APIView):
    """
    Yangi vakansiya joylashtirilganda barcha tegishli foydalanuvchilarga
    Telegram orqali xabar yuborish.
    (Bu endpoint backend/Celery task tomonidan chaqiriladi)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Vakansiya haqida bildirishnoma yuborish",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "vacancy_id": {"type": "integer"},
                },
                "required": ["vacancy_id"],
            }
        },
        responses={200: OpenApiResponse(description="Yuborildi")},
    )
    def post(self, request):
        import os
        import httpx
        from apps.vacancies.models import Vacancy
        from apps.users1.models import User

        vacancy_id = request.data.get("vacancy_id")
        if not vacancy_id:
            return Response({"error": "vacancy_id talab qilinadi"}, status=400)

        try:
            vacancy = Vacancy.objects.select_related("company").get(id=vacancy_id)
        except Vacancy.DoesNotExist:
            return Response({"error": "Vakansiya topilmadi"}, status=404)

        # Tegishli foydalanuvchilarni topish
        users_qs = User.objects.filter(
            user_type="candidate",
            chat_id__isnull=False,
            is_active=True,
        ).exclude(chat_id="")

        if vacancy.industry:
            users_qs = users_qs.filter(
                resumes__mutaxassislik__icontains=vacancy.industry
            ) | users_qs.filter(user_type="candidate")

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN_2", "")
        tg_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        ai_line = ""
        if vacancy.ai_improved_description and vacancy.ai_improved_description.startswith("http"):
            ai_line = f"\n🤖 <a href='{vacancy.ai_improved_description}'>AI Intervyuni boshlash</a>"

        text = (
            f"🔔 <b>Yangi vakansiya!</b>\n\n"
            f"🏢 <b>{vacancy.company.name}</b>\n"
            f"💼 <b>{vacancy.title}</b>\n"
            f"📂 {vacancy.industry or '—'}\n"
            f"💰 {vacancy.salary_level or 'Kelishuv boyicha'}"
            f"{ai_line}"
        )

        sent = 0
        for user in users_qs.distinct()[:500]:
            try:
                httpx.post(tg_api, json={
                    "chat_id": user.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                }, timeout=5)
                sent += 1
            except Exception:
                pass

        return Response({"sent_to": sent, "vacancy": vacancy.title})
