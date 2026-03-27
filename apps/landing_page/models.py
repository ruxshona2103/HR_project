from django.db import models

# ==========================================
# 1. Poydevor (Abstract Model)
# ==========================================
class BaseModel(models.Model):
    """Barcha modellar uchun umumiy maydonlar"""
    is_active = models.BooleanField(default=True, verbose_name="Aktivmi?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Tahrirlangan vaqt")

    class Meta:
        abstract = True


# ==========================================
# 2. Yagona nusxa (Singleton) Modellar
# ==========================================
class TeamAbout(models.Model):
    """Jamoa haqida umumiy ma'lumot (Faqat bitta yozuv)"""
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    description = models.TextField(verbose_name="Jamoa haqida batafsil")
    experience_years = models.PositiveIntegerField(default=1, verbose_name="Tajriba yili")
    team_photo = models.ImageField(upload_to='team_general/', verbose_name="Jamoaviy rasm")

    class Meta:
        verbose_name = "Jamoa ma'lumoti"
        verbose_name_plural = "Jamoa ma'lumotlari"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContactInfo(models.Model):
    """Aloqa kontaktlari (Faqat bitta yozuv)"""
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqami")
    email = models.EmailField(verbose_name="Elektron pochta")
    telegram_link = models.URLField(blank=True, verbose_name="Telegram havola")
    instagram_link = models.URLField(blank=True, verbose_name="Instagram havola")


    class Meta:
        verbose_name = "Aloqa kontakti"
        verbose_name_plural = "Aloqa kontaktlari"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Kontaktlar: {self.email} | {self.phone_number}"


# ==========================================
# 3. Dinamik (Ko'p sonli) Modellar
# ==========================================
class PlatformStep(BaseModel):
    """Saytdan foydalanish qadamlari"""
    step_number = models.PositiveIntegerField(verbose_name="Qadam tartibi")
    title = models.CharField(max_length=200, verbose_name="Qadam nomi")
    description = models.TextField(verbose_name="Qadam tavsifi")

    class Meta:
        ordering = ['step_number']
        verbose_name = "Platforma qadami"
        verbose_name_plural = "Platforma qadamlari"

    def __str__(self):
        return f"{self.step_number}. {self.title}"


class Product(BaseModel):
    """Platforma taqdim etadigan mahsulotlar/xizmatlar"""
    name = models.CharField(max_length=255, verbose_name="Mahsulot nomi")
    description = models.TextField(verbose_name="Mahsulot tavsifi")
    icon = models.ImageField(upload_to='products/', verbose_name="Ikonka")

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def __str__(self):
        return self.name


class PricingPlan(BaseModel):
    """Tarif rejalari"""
    name = models.CharField(max_length=100, verbose_name="Tarif nomi")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Narxi")
    currency = models.CharField(max_length=3, default='UZS', verbose_name="Valyuta")
    features = models.TextField(verbose_name="Imkoniyatlar", help_text="Imkoniyatlarni yangi qatordan yozing")

    class Meta:
        verbose_name = "Tarif rejasi"
        verbose_name_plural = "Tarif rejalari"

    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}"

