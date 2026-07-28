# HR Platform — Backend API

Rekruting jarayonini avtomatlashtiruvchi HR platformasi uchun backend xizmati. Django + Django REST Framework asosida qurilgan, JWT autentifikatsiya, Telegram orqali OTP-login, real-vaqt AI-intervyu (WebSocket + Google Gemini) va rezyume tahlili kabi funksiyalarni o'z ichiga oladi.

---

## 📌 Mundarija

- [Loyiha haqida](#-loyiha-haqida)
- [Texnologiyalar](#-texnologiyalar)
- [Arxitektura va ilovalar](#-arxitektura-va-ilovalar)
- [O'rnatish (lokal)](#-ornatish-lokal)
- [Environment o'zgaruvchilari](#-environment-ozgaruvchilari)
- [Telegram botlar — MUHIM](#-telegram-botlar--muhim)
- [API endpointlar](#-api-endpointlar)
- [WebSocket — AI Intervyu](#-websocket--ai-intervyu)
- [Testlar](#-testlar)
- [Health-check](#-health-check)
- [Production'ga tayyorlash uchun checklist](#-productionga-tayyorlash-uchun-checklist)
- [Ma'lum cheklovlar](#-malum-cheklovlar)

---

## 📖 Loyiha haqida

Platforma ikki turdagi foydalanuvchi bilan ishlaydi:

- **Nomzod (candidate)** — ro'yxatdan o'tadi (telefon/OTP yoki email orqali), profil/rezyume to'ldiradi, vakansiyalarni ko'radi, AI bilan mock-intervyu topshiradi.
- **Tashkilot (organization/HR)** — kompaniya profilini yaratadi, vakansiya joylaydi, nomzodlarni ko'rib chiqadi.

Autentifikatsiya **to'liq JWT (stateless)** asosida ishlaydi — Django session-based login umuman ishlatilmaydi. Bu WebSocket qismini loyihalashda hisobga olinishi kerak bo'lgan muhim arxitektura qarori (pastga qarang).

## 🛠 Texnologiyalar

| Qatlam | Texnologiya |
|---|---|
| Backend framework | Django 5.2, Django REST Framework |
| Autentifikatsiya | `djangorestframework-simplejwt` (JWT, access+refresh, blacklist) |
| Real-vaqt (WebSocket) | Django Channels 4 + Daphne (ASGI) |
| Channel layer | Redis (`channels_redis`) |
| AI | Google Gemini (`google-genai`), model: `gemini-2.0-flash` |
| Telegram | `python-telegram-bot` (2 ta alohida bot) |
| Ma'lumotlar bazasi | PostgreSQL (production) / SQLite (lokal, default) |
| API hujjatlari | drf-spectacular (Swagger / Redoc) |
| Email | SMTP (Gmail) |

## 🏗 Arxitektura va ilovalar

```
apps/
├── users1/        # Autentifikatsiya (telefon+OTP, email+kod), foydalanuvchi modeli, Telegram bog'lash
├── profile/       # Kompaniya profili, kompaniya vakansiyalari, AI-intervyu savollari
├── user_profile/  # Nomzod profili
├── vacancies/     # Vakansiyalar (CRUD, egalik permission)
├── resume/        # Rezyume va uning bo'limlari
├── landing_page/  # Ochiq (public) landing sahifa ma'lumotlari
└── ai_engine/     # AI rezyume-tekshiruv + real-vaqt AI-intervyu (WebSocket)
```

Har bir ilova o'z `models.py` / `serializers.py` / `views.py` / `urls.py` / `migrations/` tarkibiga ega — standart Django app-per-domain yondashuvi.

## ⚙️ O'rnatish (lokal)

```bash
git clone <repo-url>
cd hr-project

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp example_env .env             # keyin .env ichini to'ldiring (pastga qarang)

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput

python manage.py runserver
```

> ⚠️ **Diqqat:** loyiha Channels (WebSocket) ishlatadi. Lokal ishlab chiqishda oddiy `runserver` yetarli (Daphne avtomatik ishlaydi, chunki `daphne` `INSTALLED_APPS`da birinchi turadi), lekin **Redis lokal kompyuteringizda ishlab turishi kerak** — aks holda `CHANNEL_LAYERS` (WebSocket) ishlamaydi.

## 🔑 Environment o'zgaruvchilari

`example_env` faylida namuna bor. To'liq ro'yxat:

| O'zgaruvchi | Tavsif | Majburiymi |
|---|---|---|
| `SECRET_KEY` | Django maxfiy kaliti | ✅ (production uchun uzun, tasodifiy qiymat) |
| `DEBUG` | `True`/`False` | ✅ production'da `False` |
| `ALLOWED_HOSTS` | Vergul bilan ajratilgan domenlar/IP | ✅ production'da aniq domen kerak, `*` qoldirmang |
| `TELEGRAM_BOT_TOKEN`, `BOT_USERNAME` | Asosiy (auth/OTP) bot | ✅ |
| `TELEGRAM_BOT_TOKEN2`, `BOT_USERNAME2` | HR mock-intervyu boti (`vacansy_bot`) | ✅ |
| `GEMINI_KEY` | Google Gemini API kaliti | ✅ (AI funksiyalar uchun) |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | Gmail SMTP (email-orqali ro'yxatdan o'tish uchun) | ✅ (Gmail **App Password** ishlatilishi shart, oddiy parol emas) |
| `PLATFORM_URL` | Botlar frontendga havola berishda ishlatadigan asosiy domen | ✅ |
| `USE_POSTGRES` | `True` bo'lsa PostgreSQL, aks holda SQLite | production'da `True` tavsiya etiladi |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL ulanish ma'lumotlari | `USE_POSTGRES=True` bo'lsa ✅ |
| `REDIS_HOST`, `REDIS_PORT` | Channel layer uchun Redis | ✅ |
| `CORS_ALLOWED_ORIGINS` | Vergul bilan ajratilgan frontend domenlar | ✅ production'da (`DEBUG=False` bo'lganda) |

## 🤖 Telegram botlar — MUHIM

Loyihada **Django serveridan mustaqil**, doimiy ishlab turishi kerak bo'lgan **ikkita** Telegram bot bor. Django serverni (`runserver`/`daphne`) ishga tushirish bularni **avtomatik ishga tushirmaydi** — ular alohida process sifatida qo'lda/supervisor orqali ishga tushirilishi shart:

```bash
# 1) Auth/OTP boti (foydalanuvchi telefon orqali kirganda kod shu bot orqali yuboriladi)
python apps/users1/bot.py

# 2) HR mock-intervyu / vakansiya boti
python -m vacansy_bot.bot
```

Agar bu ikkalasi ishga tushirilmasa: telefon orqali ro'yxatdan o'tish/kirish OTP kodini hech qachon olmaydi, va Telegram orqali vakansiya boshqarish funksiyasi ishlamaydi — **Django serverning o'zi esa tashqi ko'rinishda normal ishlab turadi**, shu sababli bu holatni sezish qiyin. Deploy paytida bu ikki processni monitoring/auto-restart bilan (masalan systemd, supervisor yoki shunga o'xshash vosita orqali — tanlov deploy qiluvchi tomonda) doimiy ishlab turishini ta'minlang.

## 📡 API endpointlar

Interaktiv hujjatlar: `/swagger/` (Swagger UI) va `/redoc/`. Pastda asosiy guruhlar:

**Autentifikatsiya — telefon** (`/api/users/auth/phone/...`)
`register/candidate/` · `register/organization/` · `login/` · `verify-otp/`

**Autentifikatsiya — email** (`/api/users/auth/email/...`)
`login/` · `register/candidate/` · `register/organization/` · `verify/` · `resend-code/`

**Token / hisob** (`/api/users/...`)
`auth/token/refresh/` · `auth/logout/` · `me/` · `change-password/` · `delete-account/` · `auth/bot-link/`

**Telegram** (`/api/users/telegram/...`)
`connect/` · `disconnect/` · `status/`

**Vakansiyalar** (`/api/vacancies/vacancies/`) — standart DRF `ModelViewSet` (list/retrieve hammaga; create faqat `organization` turi uchun; update/delete faqat vakansiya egasi kompaniyaga)

**Kompaniya** (`/api/profile/...`)
`company-profile/` · `company-vacancies/` · `ai-questions/`

**Nomzod profili** (`/api/user_profile/user_profile/`)

**Rezyume** (`/api/resume/...`)
`` (asosiy) · `sections/<section>/` · `sections/<section>/<id>/`

**Landing (ochiq)** (`/api/landing_page/...`)
`landing-data/` · `products/` · `pricing/` · `contacts/`

**AI** (`/api/ai_interview/...`)
`resume-check/` · `start-interview/<vacancy_id>/` · `status/<vacancy_id>/` · `feedback/<result_id>/`

**Xizmat**
`/api/health/` — DB va cache ulanishini tekshiradi · `/admin/` — Django admin

## 🔌 WebSocket — AI Intervyu

```
ws://<domen>/ws/interview/<vacancy_id>/?token=<JWT_ACCESS_TOKEN>
```

REST API JWT (stateless) orqali ishlagani uchun, WebSocket ulanishi ham JWT'ni **query-parametr** orqali oladi (brauzer WebSocket API'si maxsus `Authorization` header qo'shishga ruxsat bermaydi) — buni `config/middleware.py`dagi `TokenAuthMiddlewareStack` bajaradi.

> ⚠️ **Ma'lum cheklov:** suhbat holati faqat WebSocket ulanishi davomida xotirada saqlanadi — ulanish uzilsa (tarmoq muammosi, sahifa yangilash), intervyu boshidan boshlanadi. Bundan tashqari, intervyu tugagach natija hozircha `InterviewResult` jadvaliga **avtomatik yozilmaydi** — bu keyingi iteratsiyada tugallanishi kerak bo'lgan ish (pastdagi "Ma'lum cheklovlar"ga qarang).

## 🧪 Testlar

```bash
python manage.py test
```

`apps/users1/Tests/` ichida telefon va email autentifikatsiya oqimlari uchun testlar mavjud.

## ❤️ Health-check

```
GET /api/health/
```
Ma'lumotlar bazasi va cache (Redis) ulanishini real vaqtda tekshiradi, monitoring/load-balancer uchun mo'ljallangan:
```json
{"status": "ok", "database": "connected", "cache": "connected"}
```

## ✅ Production'ga tayyorlash uchun checklist

Bu bo'lim faqat **kod/konfiguratsiya** darajasidagi ishlarni qamrab oladi — server, Docker, CI/CD tanlovi deploy qiluvchi tomonga tegishli.

- [ ] `.env` — barcha yuqoridagi o'zgaruvchilar real qiymatlar bilan to'ldirilgan
- [ ] `DEBUG=False`, `ALLOWED_HOSTS` — aniq domen(lar) ko'rsatilgan (`*` emas)
- [ ] `SECRET_KEY` — uzun, tasodifiy, `django-insecure-` bilan boshlanmaydigan qiymat
- [ ] PostgreSQL va Redis serverga ulangan va ishlab turibdi (`USE_POSTGRES=True`)
- [ ] `python manage.py migrate` bajarilgan
- [ ] `python manage.py collectstatic --noinput` bajarilgan
- [ ] Ikkala Telegram bot (`apps/users1/bot.py`, `vacansy_bot/bot.py`) alohida, doimiy ishlaydigan process sifatida ishga tushirilgan
- [ ] `GET /api/health/` `200 OK` qaytarayotganini tekshirish
- [ ] Gmail SMTP uchun App Password (oddiy parol emas) ishlatilgan

## ⚠️ Ma'lum cheklovlar

Halol bo'lish uchun — hozircha to'liq tugallanmagan/bilib turilgan cheklovlar:

- **AI-intervyu natijasi hali persistent emas** — suhbat WebSocket orqali ishlaydi, lekin yakuniy baholash (`AIEvaluator`) va natijani saqlash (`InterviewResult`) hali ulanmagan. `status/`, `feedback/` endpointlari shu sabab hozircha bo'sh natija qaytaradi.
- **WebSocket suhbat tarixi qayta ulanishda saqlanmaydi** — ulanish uzilsa, intervyu qaytadan boshlanadi.
- **CI/CD va konteynerizatsiya (Docker) hali qo'shilmagan** — loyiha hozircha qo'lda deploy qilinadigan holatda.