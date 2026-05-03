"""
config/urls_telegram.py  —  yoki mavjud config/urls.py ga qo'shiladi

Telegram bot endpointlari:
    /api/telegram/connect/       → Platformadan botga bog'lash (GET tekshirish, POST bog'lash)
    /api/telegram/disconnect/    → Bog'lanishni uzish
    /api/telegram/status/        → Holat
    /api/telegram/notify/        → Vakansiya bildirishnomasi (server-to-server)
"""

from django.urls import path
from apps.users1.views.telegram_connect_views import (
    TelegramConnectView,
    TelegramDisconnectView,
    TelegramStatusView,
    SendVacancyNotificationView,
)

# Bu patternlarni config/urls.py dagi urlpatterns ga qo'shing:
# path("api/", include("config.urls_telegram")),

urlpatterns = [
    path("telegram/connect/", TelegramConnectView.as_view(), name="telegram-connect"),
    path("telegram/disconnect/", TelegramDisconnectView.as_view(), name="telegram-disconnect"),
    path("telegram/status/", TelegramStatusView.as_view(), name="telegram-status"),
    path("telegram/notify/", SendVacancyNotificationView.as_view(), name="telegram-notify"),
]