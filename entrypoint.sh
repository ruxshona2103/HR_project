#!/bin/sh
set -e

# ============================================================
# entrypoint.sh — barcha xizmatlar (web, bot_auth, bot_vacancy)
# shu skript orqali ishga tushadi. Faqat "web" xizmati uchun
# migratsiya/collectstatic bajariladi — botlar buni takrorlamaydi.
# ============================================================

# --- PostgreSQL tayyor bo'lishini kutish ---
# docker-compose "depends_on: condition: service_healthy" allaqachon
# buni ta'minlaydi, lekin qo'shimcha xavfsizlik chegarasi sifatida
# (masalan Postgres "healthy" deb belgilangandan keyin ham bir necha
# millisoniya ulanishni qabul qilmasligi mumkin) qisqa retry qo'shamiz.
if [ "$USE_POSTGRES" = "True" ]; then
  echo "PostgreSQL bilan bog'lanish tekshirilmoqda ($DB_HOST:$DB_PORT)..."
  RETRIES=30
  until python -c "
import socket, sys, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect((os.environ.get('DB_HOST', 'db'), int(os.environ.get('DB_PORT', 5432))))
    sys.exit(0)
except Exception:
    sys.exit(1)
" || [ $RETRIES -eq 0 ]; do
    echo "PostgreSQL hali tayyor emas, kutilmoqda... ($RETRIES qoldi)"
    RETRIES=$((RETRIES - 1))
    sleep 1
  done
fi

# --- Faqat "web" xizmati migratsiya/collectstatic bajaradi ---
# Bot xizmatlari (bot_auth, bot_vacancy) bir xil image'dan foydalanadi,
# lekin ular ORM'ni FAQAT o'qish/yozish uchun ishlatadi — migratsiya
# ularning vazifasi emas (bir nechta konteyner bir vaqtda migratsiya
# ishga tushirsa, race condition xavfi bor).
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Migratsiyalar bajarilmoqda..."
  python manage.py migrate --noinput

  echo "Statik fayllar yig'ilmoqda..."
  python manage.py collectstatic --noinput
fi

echo "Ishga tushirilmoqda: $@"
exec "$@"
