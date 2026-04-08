#  Resume API Documentation

Ushbu loyiha **Resume (CV) boshqarish API** hisoblanadi. API orqali foydalanuvchi o‘z rezyumesini va unga tegishli bo‘limlarni (sections) yaratishi, ko‘rishi, yangilashi va o‘chirishi mumkin.

---

##  Asosiy endpointlar

###  Resume

####  Resume olish

```
GET /api/resume/resume/
```

####  Resume yaratish

```
POST /api/resume/resume/
```

####  Resume yangilash

```
PUT /api/resume/resume/
```

---

##  Bo‘limlar (Sections)

Resume ichidagi barcha bo‘limlar quyidagi endpoint orqali boshqariladi:

```
/api/resume/sections/{section}/
```

`{section}` o‘rniga quyidagi bo‘lim nomlari qo‘yiladi:

* `aloqa` (contact)
* `konikma` (skills)
* `til` (languages)
* `ishtajribasi` (work experience)
* `talim` (education)
* `sertifikat` (certificates)
* `maqola` (articles)
* `qiziqish` (interests)
* `yutuq` (achievements)

---

###  Bo‘limdagi yozuvlar ro‘yxati

```
GET /api/resume/sections/{section}/
```

---

###  Yangi yozuv qo‘shish

```
POST /api/resume/sections/{section}/
```

---

### Bitta yozuvni olish

```
GET /api/resume/sections/{section}/{id}/
```

---

### Yozuvni yangilash

```
PUT /api/resume/sections/{section}/{id}/
```

---

### Yozuvni o‘chirish

```
DELETE /api/resume/sections/{section}/{id}/
```

---

##  Texnologiyalar

* Python
* Django
* Django REST Framework

---

##  Autentifikatsiya

API ishlatish uchun foydalanuvchi autentifikatsiyadan o‘tgan bo‘lishi kerak (token yoki session orqali).

---

##  Eslatma

* Har bir foydalanuvchi faqat o‘z resyumesini boshqaradi
* `{section}` noto‘g‘ri berilsa xatolik qaytadi
* `{id}` mavjud bo‘lmagan yozuv bo‘lsa 404 qaytadi

---

##  Maqsad

Bu API yordamida:

* To‘liq resume yaratish
* Har bir bo‘limni alohida boshqarish
* Moslashuvchan va kengaytiriladigan struktura yaratish mumkin

---

##  Muallif

Loyiha: Resume API
Muallif: Husniddin

---
