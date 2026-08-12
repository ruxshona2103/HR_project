# 🤖 HR Mock Intervyu — Telegram Bot

**python-telegram-bot v20+ (async/await)**  
Django ORM bilan to'liq integratsiya. PTB `ConversationHandler` asosida qurilgan.
---

## ⚙️ O'rnatish

### 1. `.env` fayliga qo'shish:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
BOT_USERNAME=your_bot_username
PLATFORM_URL=https://yourdomain.uz
```

### 2. Botni ishga tushirish:
```bash
python -m vacancy_bot.bot

```
## 🔄 Bot ishlash oqimi

### Kandidat oqimi (1-variant — Platforma bilan bog'lash):
```
/start
  └─► Ish izlayapman / Ish beruvchiman tanlash
        └─► Platforma bilan bog'lash tugmasi
              └─► Token havolasi yuboriladi
                    └─► Foydalanuvchi platformaga kiradi → "Telegramni ulash" bosadi
                          └─► POST /api/telegram/connect/ → chat_id yoziladi
                                └─► "Bog'landim" callback → profil ko'rsatiladi
                                      └─► Tasdiqlash → Asosiy menyu
```

### Kandidat oqimi (2-variant — Login/Parol):
```
/start
  └─► Ish izlayapman tanlash
        └─► Login / Parol bilan kirish
              └─► Email yoki telefon raqam
                    └─► Parol (xabar avtomatik o'chiriladi)
                          └─► Profil tasdiqlash
                                └─► Soha to'g'riligini tekshirish
                                      └─► Asosiy menyu
```

### HR oqimi:
```
/start
  └─► Ish beruvchiman tanlash
        └─► Platformaga bog'lash YOKI Login/Parol
              └─► Tashkilot + lavozim tasdiqlash
                    └─► HR Menyu:
                          ├─► ➕ Vakansiya yaratish (10 bosqich)
                          └─► 📋 Mening vakansiyalarim
```

### Vakansiya yaratish (HR):
```
Sarlavha → Soha → Tavsif → Maosh → Bandlik turi
  → AI Intervyu qo'shish → Ko'rgazma → Tasdiqlash → Saqlash
```

### Avtomatik vakansiyalar yuborish (CRON):
```
Har kuni 09:00 + har 6 soatda:
  ├─► Barcha aktiv kandidatlar (chat_id bor)
  ├─► Har biriga sohasiga mos vakansiyalar filtrlash
  └─► Telegram orqali kartochka yuborish (AI intervyu havolasi bilan)
```

---

## 📋 Bot buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni boshlash / qayta kirish |
| `/cancel` | Joriy amaliyotni bekor qilish |
| `/vacancies` | Sohaga mos vakansiyalar ko'rish |
| `/ai_interview` | AI Intervyu sahifasiga o'tish |
| `/my_vacancies` | HR vakansiyalari ro'yxati |
| `/create_vacancy` | HR yangi vakansiya yaratish |

---

## 🔐 Xavfsizlik

- Parol kiritishda xabar avtomatik o'chiriladi (`message.delete()`)
- Platformaga bog'lash tokenlar 15 daqiqada eskiradi
- `is_valid()` — har bir token tekshiruvida ham `is_used` ham `expires_at` tekshiriladi
- Bir `chat_id` faqat bitta foydalanuvchiga biriktirilishi ta'minlanadi

---

## 🛠 Texnik stack

- `python-telegram-bot==22.6` (PTB v20+)
- `Django==5.2.1`
- `asgiref` (sync_to_async)
- `python-dotenv`

---

## ❓ Tez-tez so'raladigan savollar

**Q: Bot Django bilan bir jarayondami?**  
A: Yo'q. `bot.py` alohida process sifatida ishlaydi. Django va bot ikkalasi ham bir xil PostgreSQL bazasini ishlatadi.

**Q: Polling yoki Webhook?**  
A: Hozir `run_polling()` ishlatilgan. Production da `run_webhook()` ga o'tish tavsiya etiladi.

**Q: Celery bilan ishlatish mumkinmi?**  
A: Ha. `send_vacancies_job` funksiyasini Celery task sifatida ham ishlatish mumkin.

**Q: Yangi vakansiya qo'shilganda real-time xabar borishi uchun?**  
A: `Vacancy` modelining `post_save` signal ga yoki view ichiga  
`POST /api/telegram/notify/` chaqiruvini qo'shing.
