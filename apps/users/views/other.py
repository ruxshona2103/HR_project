import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as s


class BotLinkView(APIView):
    @extend_schema(
        tags=["Auth"],
        summary="Telegram bot linki",
        description="Telegram bot linkini qaytaradi",
        responses={200: inline_serializer("BotLinkResponse", fields={
            "bot_link": s.CharField()
        })}
    )
    def get(self, request):
        bot_username = os.getenv('BOT_USERNAME')
        return Response({"bot_link": f"https://t.me/{bot_username}"})

