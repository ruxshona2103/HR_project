# users1 — Auth App

Django REST Framework + JWT bilan to'liq auth tizimi.

## Imkoniyatlar

| Usul             | Register           | Login |
|------------------|--------------------|-------|
| 📱 Telefon (OTP) | ✅ Parolsiz         | ✅ OTP orqali |
| 📧 Email         | ✅ Email tasdiqlash | ✅ Email + Parol |



## API Endpointlar

### 📱 Telefon orqali Register (2 qadam)

**Qadam 1** — Ma'lumotlarni yuborish:
```
POST /api/users/auth/phone/register/candidate/
POST /api/users/auth/phone/register/organization/
```

**Qadam 2** — Telegram botdan kelgan OTP kodni tasdiqlash:
```
POST /api/users/auth/phone/verify-otp/
Body: {"phone_number": "+998901234567", "code": "123456"}
```

---

### 📱 Telefon orqali Login (2 qadam)

**Qadam 1** — OTP so'rash:
```
POST /api/users/auth/phone/login/
Body: {"phone_number": "+998901234567"}
```

**Qadam 2** — OTP tasdiqlash (xuddi register bilan bir xil):
```
POST /api/users/auth/phone/verify-otp/
```

---

### 📧 Email orqali Register (2 qadam)

**Qadam 1** — Ma'lumotlarni yuborish (email ga kod ketadi):
```
POST /api/users/auth/email/register/candidate/
POST /api/users/auth/email/register/organization/
```

**Qadam 2** — Emaildan kelgan kodni tasdiqlash:
```
POST /api/users/auth/email/verify/
Body: {"email": "user@gmail.com", "code": "123456"}
```

Kodni qayta yuborish:
```
POST /api/users/auth/email/resend-code/
```

---

### 📧 Email orqali Login

```
POST /api/users/auth/email/login/
Body: {"email": "user@gmail.com", "password": "StrongPass123!"}
```

---

### 🔑 Token yangilash va Logout

```
POST /api/users/auth/token/refresh/
POST /api/users/auth/logout/
```

---

### 👤 Profil

```
GET  /api/users/me/           — Profilni ko'rish
PATCH /api/users/me/          — Profilni tahrirlash
POST /api/users/change-password/
DELETE /api/users/delete-account/
```

---

### 🤖 Bot link

```
GET /api/users/auth/bot-link/
```

---

## OTP Xavfsizlik

- 5 marta xato → 10 daqiqa bloklanadi
- OTP kod 5 daqiqada eskiradi
- Bir OTP kodni faqat bir marta ishlatish mumkin

---

## Testlarni ishlatish

```bash
python manage.py test apps.users1.Tests
```
