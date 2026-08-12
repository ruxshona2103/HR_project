<div align="center">

# 🚀 HR Platform — AI-Powered Recruitment Backend

**Sun'iy intellekt yordamida rekruting jarayonini avtomatlashtiruvchi to'liq funksional backend tizim**

[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.16-red?style=flat)](https://www.django-rest-framework.org/)
[![Channels](https://img.shields.io/badge/Django%20Channels-4.3-092E20?style=flat)](https://channels.readthedocs.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![Groq](https://img.shields.io/badge/AI-Groq%20Llama%203.3-F55036?style=flat)](https://groq.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-175%20passing-brightgreen?style=flat)](#-testlar)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#-litsenziya)

</div>

---

## 📖 Loyiha haqida

**HR Platform** — nomzod va tashkilotlarni bir joyda birlashtiruvchi, sun'iy intellekt yordamida rekruting jarayonini tezlashtiruvchi backend tizim. Platforma ikkita asosiy foydalanuvchi rolini qo'llab-quvvatlaydi:

- 👤 **Nomzod (Candidate)** — telefon (Telegram OTP) yoki email orqali ro'yxatdan o'tadi, profil va rezyume to'ldiradi, vakansiyalarni ko'radi, **real-vaqt AI-intervyu** topshiradi va **AI orqali rezyumesini vakansiyaga moslik darajasini** tekshiradi.
- 🏢 **Tashkilot (HR)** — kompaniya profilini yaratadi, vakansiya joylaydi, Telegram bot orqali ham vakansiyalarni boshqaradi, nomzodlarning AI-baholangan intervyu natijalarini ko'radi.

Loyiha **production-ready** darajada ishlab chiqilgan: JWT autentifikatsiya, WebSocket orqali real-vaqt AI-suhbat, ikkita mustaqil Telegram bot, to'liq Docker-konteynerizatsiya, va **175 ta avtomatik test** bilan qamrab olingan.

### ✨ Asosiy xususiyatlar

| | |
|---|---|
| 🔐 **Ikki xil autentifikatsiya** | Email + parol (tasdiqlash kodi bilan) va Telefon + Telegram OTP |
| 🤖 **AI Mock-Intervyu** | WebSocket orqali real-vaqt, ko'p bosqichli suhbat (Groq · Llama 3.3 70B) |
| 📄 **AI Resume-Check** | Rezyumening vakansiyaga moslik foizi, kuchli/kuchsiz tomonlari |
| 💬 **2 ta Telegram bot** | OTP-login boti va HR vakansiya-boshqaruv boti (kunlik avtomatik xabarnoma bilan) |
| 🏢 **Kompaniya va vakansiya boshqaruvi** | To'liq CRUD, egalik-asosidagi ruxsatlar (permissions) |
| 📊 **Swagger / Redoc** | `drf-spectacular` orqali avtomatik, interaktiv API hujjatlari |
| 🐳 **Docker-ready** | `Dockerfile`, `docker-compose.yml`, Nginx reverse-proxy — bitta buyruq bilan deploy |
| ✅ **175 ta test** | Har bir asosiy modul (auth, vakansiya, profil, resume, AI) test bilan qamrab olingan |

---

## 🏗 Arxitektura

```
                         ┌──────────────┐
                         │    Nginx     │  ← SSL, static/media, reverse-proxy
                         └──────┬───────┘
                                │
                   ┌────────────┴────────────┐
                   │                         │
            HTTP/REST API              WebSocket (/ws/)
                   │                         │
                   └────────────┬────────────┘
                                │
                       ┌────────▼────────┐
                       │  Daphne (ASGI)   │  ← Django + DRF + Channels
                       └───┬─────────┬────┘
                            │         │
                  ┌─────────▼──┐   ┌──▼──────────┐
                  │ PostgreSQL │   │    Redis     │  ← Channel layer
                  └────────────┘   └─────────────┘

        ┌─────────────────────┐   ┌──────────────────────┐
        │  Telegram Bot #1     │   │  Telegram Bot #2      │
        │  (OTP / Auth)        │   │  (HR / Vakansiyalar)  │
        │  — alohida process   │   │  — alohida process    │
        └───────────┬──────────┘   └───────────┬───────────┘
                     └──────────────┬───────────┘
                                     │
                              PostgreSQL (umumiy)
```

Har ikkala Telegram bot Django ilovasidan **mustaqil, doimiy ishlaydigan process** sifatida ishlaydi (`python-telegram-bot`, long-polling) — Docker'da alohida konteyner (`bot_auth`, `bot_vacancy`) sifatida ishga tushiriladi.

### Django ilovalari (apps)

| Ilova | Vazifasi |
|---|---|
| `users1` | Autentifikatsiya (telefon+OTP, email+kod), foydalanuvchi modeli, Telegram akkaunt bog'lash |
| `user_profile` | Nomzod profili |
| `profile` | Kompaniya profili, kompaniya vakansiyalari, AI-intervyu savollari banki |
| `vacancies` | Vakansiyalar — CRUD, egalik (ownership) asosidagi ruxsatlar |
| `resume` | Rezyume va uning bo'limlari (ta'lim, tajriba, ko'nikmalar va h.k.) |
| `landing_page` | Ochiq (public) landing-sahifa ma'lumotlari (mahsulotlar, narxlar, kontaktlar) |
| `ai_engine` | AI rezyume-tekshiruv (REST) + real-vaqt AI-intervyu (WebSocket, Groq) |

---

## 🛠 Texnologiyalar stack'i

<table>
<tr><td><b>Backend</b></td><td>Python 3.12, Django 5.2, Django REST Framework</td></tr>
<tr><td><b>Autentifikatsiya</b></td><td>JWT (djangorestframework-simplejwt) — access + refresh + blacklist</td></tr>
<tr><td><b>Real-vaqt</b></td><td>Django Channels 4 + Daphne (ASGI) + Redis (channel layer)</td></tr>
<tr><td><b>Sun'iy intellekt</b></td><td>Groq API — <code>llama-3.3-70b-versatile</code> (async va sync client'lar)</td></tr>
<tr><td><b>Telegram</b></td><td>python-telegram-bot v22 (2 ta mustaqil bot, job-queue bilan)</td></tr>
<tr><td><b>Ma'lumotlar bazasi</b></td><td>PostgreSQL 16 (production) / SQLite (lokal dev)</td></tr>
<tr><td><b>Email</b></td><td>Resend API (tasdiqlash kodlari uchun)</td></tr>
<tr><td><b>API hujjatlari</b></td><td>drf-spectacular (OpenAPI 3 / Swagger / Redoc)</td></tr>
<tr><td><b>Konteynerizatsiya</b></td><td>Docker, Docker Compose, Nginx, Let's Encrypt (certbot)</td></tr>
<tr><td><b>Testlar</b></td><td>Django TestCase / DRF APIClient / Channels WebsocketCommunicator — 175 ta test</td></tr>
</table>

---

## ⚙️ O'rnatish

### A) Docker orqali (tavsiya etiladi)

```bash
git clone <repo-url> && cd hr-project
cp example_env .env      # va qiymatlarni to'ldiring
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```
To'liq, bosqichma-bosqich production-deploy qo'llanmasi (SSL, backup, monitoring) — [`DEPLOY.md`](./DEPLOY.md) faylida.

### B) Lokal (Docker'siz)

```bash
git clone <repo-url> && cd hr-project
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp example_env .env      # va qiymatlarni to'ldiring

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver
```

> ⚠️ Loyiha WebSocket (Channels) ishlatadi — **Redis lokal kompyuteringizda ishlab turishi shart**, aks holda AI-intervyu funksiyasi ishlamaydi.

Telegram botlarni alohida, mustaqil process sifatida ishga tushiring (Django serverdan mustaqil):
```bash
python apps/users1/bot.py        # OTP / autentifikatsiya boti
python vacancy_bot/bot.py        # HR / vakansiya boti
```

---

## 🔑 Environment o'zgaruvchilari

| O'zgaruvchi | Tavsif |
|---|---|
| `SECRET_KEY` | Django maxfiy kaliti (production'da uzun, tasodifiy qiymat) |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | Vergul bilan ajratilgan domenlar/IP |
| `TELEGRAM_BOT_TOKEN`, `BOT_USERNAME` | Asosiy (auth/OTP) bot |
| `TELEGRAM_BOT_TOKEN2`, `BOT_USERNAME2` | HR / vakansiya boti |
| `GROQ_API_KEY` | Groq API kaliti (AI-intervyu, resume-check) |
| `RESEND_API_KEY`, `DEFAULT_FROM_EMAIL` | Email (tasdiqlash kodlari) uchun |
| `PLATFORM_URL` | Botlar frontendga havola berishda ishlatadigan asosiy domen |
| `USE_POSTGRES` | `True` bo'lsa PostgreSQL, aks holda SQLite |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL ulanish ma'lumotlari |
| `REDIS_HOST`, `REDIS_PORT` | Channel layer uchun Redis |
| `CORS_ALLOWED_ORIGINS` | Frontend domen(lar)i |

To'liq namuna: [`example_env`](./example_env) (lokal) yoki [`.env.docker.example`](./.env.docker.example) (Docker).

---

## 📡 API endpointlar

Interaktiv hujjatlar ishga tushirilgandan so'ng mavjud: **`/swagger/`**, **`/redoc/`**, OpenAPI sxema — **`/api/schema/`**.

<details>
<summary><b>🔐 Autentifikatsiya — telefon</b> (<code>/api/users/auth/phone/...</code>)</summary>

| Method | Endpoint | Tavsif |
|---|---|---|
| POST | `register/candidate/` | Nomzod sifatida ro'yxatdan o'tish |
| POST | `register/organization/` | Tashkilot sifatida ro'yxatdan o'tish |
| POST | `login/` | Telefon orqali kirish so'rovi |
| POST | `verify-otp/` | Telegram bot yuborgan OTP kodni tasdiqlash |
</details>

<details>
<summary><b>📧 Autentifikatsiya — email</b> (<code>/api/users/auth/email/...</code>)</summary>

| Method | Endpoint | Tavsif |
|---|---|---|
| POST | `login/` | Email + parol bilan kirish |
| POST | `register/candidate/` | Nomzod — 1-qadam (kod yuboriladi) |
| POST | `register/organization/` | Tashkilot — 1-qadam |
| POST | `verify/` | Tasdiqlash kodi — 2-qadam (JWT qaytadi) |
| POST | `resend-code/` | Kodni qayta yuborish |
</details>

<details>
<summary><b>👤 Hisob boshqaruvi</b> (<code>/api/users/...</code>)</summary>

| Method | Endpoint | Tavsif |
|---|---|---|
| POST | `auth/token/refresh/` | JWT access tokenni yangilash |
| POST | `auth/logout/` | Chiqish (refresh token blacklist) |
| GET/PATCH | `me/` | Joriy foydalanuvchi ma'lumotlari |
| POST | `change-password/` | Parolni almashtirish |
| DELETE | `delete-account/` | Hisobni o'chirish |
| POST | `auth/bot-link/` | Botga bog'lash uchun token olish |
</details>

<details>
<summary><b>📲 Telegram</b> (<code>/api/users/telegram/...</code>)</summary>

| Method | Endpoint | Tavsif |
|---|---|---|
| GET/POST | `connect/` | Telegram akkauntni bog'lash |
| POST | `disconnect/` | Bog'lanishni uzish |
| GET | `status/` | Bog'lanish holati |
</details>

<details>
<summary><b>💼 Vakansiyalar va kompaniya</b></summary>

| Method | Endpoint | Tavsif |
|---|---|---|
| GET | `/api/vacancies/vacancies/` | Barcha vakansiyalar ro'yxati (ochiq) |
| POST | `/api/vacancies/vacancies/` | Yangi vakansiya (faqat tashkilot) |
| GET/PUT/PATCH/DELETE | `/api/vacancies/vacancies/{id}/` | Vakansiya detali (faqat egasi o'zgartiradi) |
| GET/PUT/PATCH | `/api/profile/company-profile/` | Kompaniya profili |
| GET | `/api/profile/company-vacancies/` | Kompaniyaning o'z vakansiyalari + moslik ballari |
| GET/POST | `/api/profile/ai-questions/` | AI-intervyu savollari banki |
</details>

<details>
<summary><b>📄 Nomzod profili va rezyume</b></summary>

| Method | Endpoint | Tavsif |
|---|---|---|
| GET/PUT/PATCH | `/api/user_profile/user_profile/` | Nomzod profili |
| GET/PUT/PATCH | `/api/resume/` | Asosiy rezyume ma'lumotlari |
| GET/POST | `/api/resume/sections/{section}/` | Rezyume bo'limi (masalan `education`, `experience`) |
| GET/PUT/PATCH/DELETE | `/api/resume/sections/{section}/{id}/` | Bo'lim yozuvi detali |
</details>

<details>
<summary><b>🌐 Landing (ochiq, autentifikatsiyasiz)</b></summary>

| Method | Endpoint | Tavsif |
|---|---|---|
| GET | `/api/landing_page/landing-data/` | Barcha landing ma'lumoti (bitta so'rovda) |
| GET | `/api/landing_page/products/` | Mahsulotlar |
| GET | `/api/landing_page/pricing/` | Narx rejalari |
| GET | `/api/landing_page/contacts/` | Kontakt ma'lumotlari |
</details>

<details>
<summary><b>🤖 AI Engine</b> (<code>/api/ai_interview/...</code>)</summary>

| Method | Endpoint | Tavsif |
|---|---|---|
| POST | `resume-check/` | Rezyumeni vakansiyaga moslik bo'yicha AI tahlili |
| GET | `start-interview/{vacancy_id}/` | Intervyuni boshlash uchun ma'lumot (WebSocket URL) |
| GET | `status/{vacancy_id}/` | Nomzodning shu vakansiya bo'yicha intervyu holati |
| GET | `feedback/{result_id}/` | AI baholash natijasi va xulosasi (faqat egasi ko'radi) |
</details>

**Xizmat endpointlari:** `GET /api/health/` — DB va Redis ulanishini tekshiradi · `/admin/` — Django admin panel.

---

## 🔌 WebSocket — Real-vaqt AI Intervyu

```
ws://<domen>/ws/interview/<vacancy_id>/?token=<JWT_ACCESS_TOKEN>
```

JWT (stateless autentifikatsiya) WebSocket ulanishida **query-parametr** orqali uzatiladi — brauzer WebSocket API'si maxsus `Authorization` header qo'shishga ruxsat bermagani uchun, `config/middleware.py`dagi maxsus `TokenAuthMiddlewareStack` buni o'qib, foydalanuvchini autentifikatsiya qiladi.

**Suhbat oqimi:**
1. Klient ulanadi → AI salomlashuv xabarini yuboradi
2. Nomzod javob yozadi → AI keyingi savolni beradi (5–7 savolgacha, kontekst asosida)
3. AI suhbatni yakunlasa (yoki xavfsizlik chegarasi — 15 ta murojaatga yetsa) → suhbat avtomatik **baholanadi** (Groq orqali, JSON formatida ball + xulosa) va natija `InterviewResult` jadvaliga saqlanadi
4. Natijani `GET /api/ai_interview/feedback/{result_id}/` orqali olish mumkin

Arxitektura jihatdan muhim: tarmoq (Groq) chaqiruvlari **to'g'ridan-to'g'ri asinxron** (`AsyncGroq`, `await`) bajariladi, ma'lumotlar bazasi operatsiyalari esa Django'ning tabiiy async ORM metodlari (`aget`, `acreate`) orqali — event loop hech qachon bloklanmaydi.

---

## ✅ Testlar

```bash
python manage.py test
```

**175 ta test**, quyidagi modullarni qamrab oladi: autentifikatsiya (telefon/email/Telegram), vakansiyalar (CRUD + ruxsatlar), kompaniya/nomzod profillari, rezyume, landing-page, AI engine (WebSocket suhbat simulyatsiyasi bilan).

---

## 🐳 Deploy

Loyiha to'liq Docker-konteynerizatsiya qilingan: `web` (Daphne), `bot_auth`, `bot_vacancy`, `db` (PostgreSQL), `redis`, `nginx` — har biri alohida xizmat sifatida `docker-compose.yml`da tavsiflangan. SSL (Let's Encrypt), backup, monitoring bo'yicha to'liq bosqichma-bosqich yo'riqnoma — **[`DEPLOY.md`](./DEPLOY.md)**.

## 🔄 CI/CD

`main` branch'ga har bir `push`da avtomatik ravishda:
1. **Test** — 175 ta test PostgreSQL + Redis service konteynerlari bilan ishga tushiriladi (migratsiya sinxronligi ham tekshiriladi)
2. **Build** — testlar o'tsa, Docker image quriladi va GitHub Container Registry (GHCR)ga yuboriladi
3. **Deploy** — image tayyor bo'lgach, SSH orqali production serverga avtomatik joylashtiriladi

Pull Request'larda faqat 1-bosqich (test) ishlaydi — deploy qilinmaydi. Workflow: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)
---

## 🔒 Xavfsizlik

- JWT (access + refresh, avtomatik rotatsiya va blacklist)
- Ma'lum bir foydalanuvchi turiga (`candidate` / `organization`) xos ruxsatlar
- Vakansiyalarni faqat egasi tahrirlashi/o'chirishi mumkin (`IsVacancyOwnerOrReadOnly`)
- OTP/email-kod so'rovlari uchun alohida throttling (`5/min`)
- Production'da avtomatik yoqiladigan xavfsizlik header'lari (HSTS, SSL redirect, secure cookies)
- CORS — production'da faqat ruxsat etilgan domenlar
- Barcha maxfiy ma'lumotlar (`SECRET_KEY`, API kalitlar, DB parollar) environment o'zgaruvchilari orqali, koddan ajratilgan

---

## 📁 Loyiha tuzilishi

```
hr-project/
├── apps/
│   ├── users1/            # Autentifikatsiya, foydalanuvchi, Telegram bog'lash
│   ├── user_profile/      # Nomzod profili
│   ├── vacancies/         # Vakansiyalar
│   ├── profile/           # Kompaniya profili
│   ├── landing_page/      # Ochiq landing ma'lumotlari
│   ├── resume/            # Rezyume
│   └── ai_engine/         # AI resume-check + WebSocket intervyu
├── config/                # Django sozlamalari, urls, asgi/wsgi, middleware
├── vacancy_bot/           # HR Telegram boti
├── Dockerfile / docker-compose.yml / nginx.conf
├── README.md              # Loyiha haqida ma'lumot
└── requirements.txt
```

---

## 👥 Mualliflar

Loyiha ustida birgalikda ish olib borgan dasturchilar jamoasi:

<table>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/ali-hidirov-09">
        <img src="https://github.com/ali-hidirov-09.png" width="100px;" alt="Xidirov Ali"/><br />
        <sub><b>Xidirov Ali</b></sub>
      </a><br />
      <small> Team Lead / Backend Developer /  Ai Engineer / QA Tester</small>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/ruxshona2103">
        <img src="https://github.com/ruxshona2103.png" width="100px;" alt="A'lamxo'jayeva Ruxshona"/><br />
        <sub><b>Ruxshona</b></sub>
      </a><br />
      <small>Tema Lead</small>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/baxtiyorovanozima02">
        <img src="https://github.com/baxtiyorovanozima02.png" width="100px;" alt="Baxtiyorova Nozima"/><br />
        <sub><b>Baxtiyorova Nozima</b></sub>
      </a><br />
      <small>Backend Developer / DevOps / QA Tester</small>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/Tolqinovjahongir18-debug">
        <img src="https://github.com/Tolqinovjahongir18-debug.png" width="100px;" alt="To'lqinov Jahongir"/><br />
        <sub><b>To'lqinov Jahongir</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/BekzodAsqarov">
        <img src="https://github.com/BekzodAsqarov.png" width="100px;" alt="Asqarov Bekzod"/><br />
        <sub><b>Asqarov Bekzod</b></sub>
      </a><br />
      <small>Ai Engineer</small>
    </td>
  </tr>
  <tr>
    <td align="center" width="20%">
          <a href="https://github.com/Rashidova95">
        <img src="https://github.com/Rashidova95.png" width="100px;" alt="Rashidova Surayyo"/><br />
        <sub><b>Rashidova Surayyo</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/xujamshukirov-dev">
        <img src="https://github.com/xujamshukirov-dev.png" width="100px;" alt="Xujamshukirov Xusniddin"/><br />
        <sub><b>Xujamshukirov Xusniddin</b></sub>
      </a><br />
      <small>Backend developer</small>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/Miraziz-Coder">
        <img src="https://github.com/Miraziz-Coder.png" width="100px;" alt="Mirazimov Miraziz"/><br />
        <sub><b>Mirazimov Miraziz</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/Husan2007-ku">
        <img src="https://github.com/Husan2007-ku.png" width="100px;" alt="Malikov Husan"/><br />
        <sub><b>Malikov Husan</b></sub>
      </a><br />
      <small>Technical Writer</small>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/maxmudovferuz78-pixel">
        <img src="https://github.com/maxmudovferuz78-pixel.png" width="100px;" alt="Maxmudov Feruz"/><br />
        <sub><b>Maxmudov Feruz</b></sub>
      </a><br />
      <small>Backend Developer</small>
    </td>
  </tr>
</table>

## 📄 Litsenziya

MIT
