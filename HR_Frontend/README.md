# Ishga.AI — Frontend (HR_project uchun)

Bu papka **HR_project-main** (Django + DRF) backendi uchun yozilgan, alohida, to'liq ishlaydigan
frontend ilova. Vanilla JavaScript (ES modules) bilan yozilgan — hech qanday build qadam (npm/webpack)
talab qilinmaydi, shuning uchun Nginx/Coolify ostida statik fayl sifatida osongina joylashtiriladi.

## Ishga tushirish

1. Backend loyihani (`HR_project-main`) odatdagidek ishga tushiring:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
2. Backendda `settings.py` da `CORS_ALLOW_ALL_ORIGINS = DEBUG` bor — `DEBUG=True` bo'lsa barcha originlarga
   ruxsat beriladi, frontendni istalgan portdan ochsangiz ham ishlayveradi.
3. Bu papkani istalgan statik server bilan oching (masalan VS Code Live Server, yoki):
   ```bash
   cd HR_frontend
   python -m http.server 5500
   ```
   va brauzerda `http://127.0.0.1:5500` ni oching.
4. Agar backend boshqa manzilda (masalan Coolify orqali production domenda) ishlasa —
   sayt ichida **pastki footer → "API sozlamalari"** (`#/settings/api`) orqali API manzilini
   o'zgartiring. Standart qiymat: `http://127.0.0.1:8000/api`.

## Nima qilingan (tahlil xulosasi)

Backendni to'liq o'qib chiqib, quyidagi API'lar frontendga ulandi:

| Modul | Endpoint(lar) | Frontendda |
|---|---|---|
| Email autentifikatsiya | `register/candidate`, `register/organization`, `verify`, `resend-code`, `login` | `#/register/*`, `#/verify`, `#/login` |
| Telefon autentifikatsiya (Telegram OTP) | `phone/register/*`, `phone/login`, `phone/verify-otp` | `#/phone-auth` |
| JWT | `token/refresh`, `logout` | `api.js` avtomatik yangilaydi |
| Profil | `me` (GET/PATCH), `change-password`, `delete-account`, `bot-link`, `telegram/*` | `#/settings` |
| Landing sahifa | `landing-data`, `products`, `pricing`, `contacts` | `#/` (bosh sahifa) |
| Vakansiyalar (umumiy) | `vacancies/vacancies/` | `#/vacancies` |
| Kompaniya profili va vakansiyalari | `profile/company-profile/me/`, `profile/company-vacancies/` | `#/employer/*` |
| AI intervyu savollari | `profile/ai-questions/` | `#/employer/questions` |
| Rezyume | `resume/`, `resume/sections/<section>/...` (8 ta bo'lim) | `#/candidate/resume` |
| AI rezyume tekshiruvi | `ai_interview/resume-check/` | `#/candidate/ai-check` |
| AI intervyu (WebSocket) | `ai_interview/start-interview/<id>/` + `ws/interview/<id>/` | `#/candidate/interview/:id` |

## Tahlil paytida topilgan backend muammolari (frontendga ulanmadi)

Bularni frontendga qo'shmadim, chunki ular hozircha ishlamaydi yoki xavfsizlik nuqtai
nazaridan noto'g'ri — backend tomonda tuzatish tavsiya etiladi:

1. **`apps/choose_roles`** — `views.py`/`urls.py` mavjud va `INSTALLED_APPS`da bor, lekin
   `config/urls.py`ga **ulanmagan** (`include("apps.choose_roles.urls")` qatori yo'q). Hozircha
   `/api/choose-roles/choose-role/` kabi so'rov 404 qaytaradi. Amalda ham foydalanuvchi turi
   (`candidate`/`organization`) allaqachon ro'yxatdan o'tishda belgilanadi, shu sababli bu app
   umuman ishlatilmayotganga o'xshaydi.
2. **`apps/candidates`** — `INSTALLED_APPS`da yo'q va main `urls.py`ga ham ulanmagan — butunlay
   "o'lik" kod (`get_my_profile`, `ai_resume_check`).
3. **`apps/user_profile`** — `UserProfile` modelida foydalanuvchiga bog'lovchi (`ForeignKey`/`OneToOne`)
   maydon yo'q, va `UserProfileViewSet.queryset = UserProfile.objects.all()` — ya'ni har qanday
   login qilgan foydalanuvchi **barcha** foydalanuvchilarning ta'lim ma'lumotlarini ko'rishi/o'zgartirishi
   mumkin. Xavfsizlik nuqtai nazaridan tuzatilmaguncha frontendga ulamadim.
4. **Vakansiyalarga "murojaat qilish" (apply) endpoint'i yo'q** — backendda faqat vakansiya
   CRUD, AI rezyume tekshiruvi va AI intervyu bor. Shu sababli frontendda "Apply" tugmasi yo'q;
   o'rniga "AI rezyume tekshiruvi" va "AI intervyu boshlash" tugmalari qo'yildi.
5. `VacancySerializer`dagi `match_score` maydoni `Candidate` modeliga (demo, userga bog'lanmagan)
   tayanadi — frontendda ishlatilmadi, o'rniga har bir vakansiya uchun to'liq AI rezyume
   tekshiruvi taklif qilindi.
6. **`VacancyViewSet`da (`apps/vacancies`) `permission_classes` yo'q** — global sozlama
   (`IsAuthenticated`) qo'llanadi, ya'ni **login qilmagan foydalanuvchi vakansiyalar ro'yxatini
   umuman ko'ra olmaydi**. Shu sababli `#/vacancies` sahifasi endi login talab qiladi (guard
   qo'shildi). Bundan tashqari, bu ViewSet hech qanday egalik tekshiruvi qilmaydi — nazariy
   jihatdan istalgan login qilgan foydalanuvchi (hatto boshqa kompaniyaning) `/api/vacancies/vacancies/<id>/`
   orqali istalgan vakansiyani o'chirishi/tahrirlashi mumkin. Frontend ataylab faqat to'g'ri
   cheklangan `profile/company-vacancies/` endpoint'idan foydalanadi — bu xavfsizlik teshigini
   backendda `permission_classes` va `get_queryset` bilan tuzatish tavsiya etiladi.
7. **`apps/users1/views/telegram_connect_views.py`** — bu faylda ham `TelegramConnectView`/
   `TelegramDisconnectView`/`TelegramStatusView`/`SendVacancyNotificationView` bor, lekin
   `config/urls.py` amalda **boshqa** fayldan (`telegram_connect.py`) import qiladi. Demak
   `telegram_connect_views.py` — deyarli bir xil, ammo ishlatilmayotgan dublikat fayl, va
   `SendVacancyNotificationView` (vakansiya haqida Telegram orqali xabar yuborish) **umuman
   ulanmagan** — kerak bo'lsa uni `config/urls.py`ga qo'shish kerak bo'ladi.

## Ushbu versiyada tuzatilgan frontend xatolari

Birinchi versiyada test qilinganda topilgan, endi tuzatilgan muammolar:

- **[KRITIK] Vakansiya qo'shish ishlamasdi**: `Vacancy.status` va `Vacancy.daily_hours`
  maydonlari `blank=True`siz — forma bo'sh tanlovni `null` qilib yuborgani uchun backend har
  doim 400 xatolik qaytarardi. Endi bo'sh maydonlar butunlay yuborilmaydi (`formkit.js`).
- Vakansiya formasida yetishmayotgan maydonlar qo'shildi: **ish turi (work_formats — bir nechta
  tanlov, chip ko'rinishida)**, xarita koordinatalari (`map_lat`/`map_lng`), AI tavsif
  (`ai_improved_description`).
- Sozlamalar sahifasida Telegram holati noto'g'ri maydon nomi bilan tekshirilardi
  (`connected` o'rniga backend `is_linked` qaytaradi) — tuzatildi.
- `#/vacancies` sahifasi endi backend haqiqatiga mos ravishda login talab qiladi (yuqoridagi
  6-band).

## Papka tuzilishi

```
HR_frontend/
├── index.html
├── css/style.css        — dizayn tizimi (ranglar, tipografiya, komponentlar)
├── js/
│   ├── config.js         — API manzili + barcha endpoint yo'llari
│   ├── api.js             — fetch wrapper, JWT avtomatik yangilanishi
│   ├── store.js           — sessiya (token/user) localStorage'da
│   ├── router.js          — hash-based routing
│   ├── nav.js             — yuqori navigatsiya (rolga qarab)
│   ├── components.js      — toast, modal, "AI moslik" gauge va boshqalar
│   ├── formkit.js         — forma maydonlarini generatsiya qilish
│   ├── app.js             — barcha route'larni ulash
│   └── pages/
│       ├── landing.js     — bosh sahifa (jonli backend ma'lumoti bilan)
│       ├── auth.js        — kirish / ro'yxatdan o'tish / tasdiqlash
│       ├── vacancies.js   — vakansiyalar ro'yxati
│       ├── candidate.js   — nomzod paneli, rezyume, AI tekshiruv, AI intervyu
│       ├── employer.js    — kompaniya paneli, vakansiyalar, AI savollar
│       └── settings.js    — profil, parol, Telegram, API sozlamalari
└── README.md
```

## Dizayn ilhomi — career.edu.uz

Foydalanuvchi taqdim etgan skrinshotlar asosida quyidagi tuzilma **career.edu.uz** saytiga
o'xshab qurildi (ranglar va shrift esa loyihaning o'z uslubida — zumrad-yashil/oltin,
Fraunces/Manrope — qoldirildi):

- **Hero banner** — to'liq enli rangli fon, ikki qatorli sarlavha, statistik "pill" belgilar,
  ikkita CTA tugma va o'ng tomonda vizual blok.
- **"Eng so'nggi vakansiyalar"** bo'limi — bosh sahifada haqiqiy (yoki, mehmon uchun, aniq
  "namuna" deb belgilangan) vakansiya kartalari: "Yangi" belgisi, saqlash ikonkasi, teglar
  qatori, maosh, qisqa tavsif, "Ko'proq" havolasi, kompaniya nomi, manzil va statistika.
- **"Platforma haqida"** va **"AI imkoniyatlari"** — rangli ikon-quti + sarlavha + tavsif
  formatidagi kartalar qatori.
- Pastki **CTA banner** (hero uslubidagi qisqa blok) va **ko'p ustunli footer**.
- **Vakansiyalar sahifasi** — chap tomonda to'liq filtr paneli (hudud, ish joyi, tajriba,
  ta'lim darajasi, bandlik turi) + o'ng tomonda karta setkasi, xuddi original saytdagidek.
- **Kirish oqimi** — avval "Foydalanuvchi turini tanlang" (Nomzod / Tashkilot) katta kartali
  ekran, so'ng tanlangan turga mos login/ro'yxatdan o'tish formasi.
- **Pastki o'ng burchakdagi suzuvchi AI yordamchi tugmasi** — bosilganda tezkor havolalar
  paneli ochiladi (vakansiya qidirish, AI rezyume tekshiruvi, rezyume tuzish).

**Ataylab ko'chirilmagan qismlar:** original saytdagi **Frilanserlar**, **Tadbirlar** va
**Karyera markazlari** bo'limlari — bu loyihaning backendida bunga mos endpoint yo'q. Soxta/
ishlamaydigan bo'limlar yaratmaslik uchun ular qo'shilmadi. Shuningdek, original saytning
davlat ID (prof.edu.uz/HEMIS) orqali kirish tizimi o'rniga o'zimizning email/telefon
autentifikatsiyamiz ishlatildi, chunki bu backendda shunday joriy etilgan.

## Dizayn yo'nalishi

- **Palitra**: chuqur o'rmon-ko'mir foni (`#0d1512`), zumrad-yashil asosiy rang (o'sish/ishga
  qabul qilinish ramzi), oltin aksent (yutuq/muvaffaqiyat lahzalari uchun).
- **Tipografika**: sarlavhalar uchun *Fraunces* (serif, xarakterli), matn/UI uchun *Manrope*,
  raqamli ma'lumotlar (ballar, IDlar) uchun *IBM Plex Mono*.
- **Signatura elementi**: "AI moslik" yarim doira gauge — bosh sahifada demo sifatida, keyin
  AI rezyume tekshiruvi natijasida qayta ishlatiladi — bu platformaning asosiy g'oyasini
  (AI orqali moslikni o'lchash) vizual tilga aylantiradi.

## Eslatmalar

- **Backend'ni ishga tushirishda `table "vacancies_candidate" already exists` xatosi chiqsa**:
  `apps/vacancies/migrations/0002_candidate_alter_vacancy_type.py` fayli `Candidate` jadvalini
  `0001_initial.py` bilan **ikki marta** yaratadi. `db.sqlite3`ni o'chirib qaytadan
  `migrate` qiling, yoki `0002` migratsiyasidan `Candidate`ni yaratuvchi qismini qo'lda
  o'chirib tashlang (faqat `type` maydoniga oid `AlterField` qismini qoldiring).
- WebSocket intervyu ishlashi uchun backendda **Django Channels / ASGI server** (`daphne` yoki
  `uvicorn`) ishga tushirilgan bo'lishi kerak — oddiy `runserver` WebSocket'ni qo'llab-quvvatlamaydi.
- Profil rasmini (`profil_rasm`) yuklash frontendda hozircha qo'shilmagan — keyingi bosqichda
  `multipart/form-data` bilan osongina qo'shish mumkin.
- Barcha matnlar o'zbek tilida yozilgan.
