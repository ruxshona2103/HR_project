from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Resume(models.Model):
    """Nomzodning asosiy resume kartochkasi"""
    foydalanuvchi = models.ForeignKey(

        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resume',
        verbose_name='Foydalanuvchi'
    )
    mutaxasislik = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Mutaxasislik sohasi'
    )
    lavozim = models.CharField(
        max_length=150,
        verbose_name='Joriy lavozim/Maqsadli lavozim',
    )
    men_haqimda = models.TextField(
        blank=True,
        verbose_name='Men haqimda'
    )
    profil_rasm = models.ImageField(
        upload_to='resume/rasmlar/',
        null=True,blank=True,
        verbose_name='Profil rasmi'
    )
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumelar'

    def __str__(self):
        return f"{self.foydalanuvchi.get_full_name()} - {self.lavozim}"



class Aloqa(models.Model):
    """Nomzodning aloqa malumotlari"""
    resume = models.OneToOneField(
        Resume,on_delete=models.CASCADE,
        related_name='aloqa',
        verbose_name='Resume'
    )

    telefon = models.CharField(
        max_length=20,
        verbose_name='Telefon raqam'
    )
    email = models.EmailField(
        verbose_name='Email pochta'

    )
    shahar = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Shahar / Viloyat'
    )
    telegram = models.CharField(
        max_length=100, blank=True,
        verbose_name='Telegram'
    )
    linkedin = models.URLField(
        blank=True,
        verbose_name='LinkideIn'

    )
    github = models.URLField(
        blank=True,
        verbose_name='GitHub'
    )
    portfolio_url = models.URLField(
        blank=True,
        verbose_name='Portfolio sayti'
    )

    class Meta:
        verbose_name = 'Aloqa'
        verbose_name_plural = 'Aloqa ma\'lumotlari'

    def __str__(self):
        return f"{self.resume} - Aloqa"

class Konikma(models.Model):
    """Nomzod ko'nikmalari"""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='konikmalar',
        verbose_name='Resume'
    )
    nom = models.CharField(
        max_length=100,
        verbose_name='Ko\'nikma nomi'
    )
    daraja = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Daraja'
    )
    kategoriya = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Kategoriya (masalan: Dasturlash tillari, Vositalar)'
    )

    class Meta:
        verbose_name = 'Ko\'nikma'
        verbose_name_plural = 'Ko\'nikmalar'

    def __str__(self):
        return f"{self.nom} ({self.get_daraja_display()})"



class Til(models.Model):
    """Nomzod biladigan tillar"""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='tillar',
        verbose_name='Resume'
    )
    til_nomi = models.CharField(
        max_length=50,
        verbose_name='Til nomi'
    )
    daraja = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Bilish darajasi'
    )

    class Meta:
        verbose_name = 'Til'
        verbose_name_plural = 'Tillar'

    def __str__(self):
        return f"{self.til_nomi} - {self.get_daraja_display()}"



class IshTajribasi(models.Model):
    """Nomzodning ish tajribasi"""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='ish_tajribalari',
        verbose_name='Resume'
    )
    kompaniya_nomi = models.CharField(
        max_length=150,
        verbose_name='Kompaniya nomi'
    )
    lavozim = models.CharField(
        max_length=150,
        verbose_name='Lavozim'
    )
    ish_turi = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Ish turi'
    )
    boshlanish_sanasi = models.DateField(
        verbose_name='Boshlanish sanasi'
    )
    tugash_sanasi = models.DateField(
        null=True, blank=True,
        verbose_name='Tugash sanasi'
    )
    hozir_ishlayapman = models.BooleanField(
        default=False,
        verbose_name='Hozir shu yerda ishlayapman'
    )
    tavsif = models.TextField(
        blank=True,
        verbose_name='Vazifalar va yutuqlar tavsifi'
    )
    shahar = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Shahar'
    )

    class Meta:
        verbose_name = 'Ish tajribasi'
        verbose_name_plural = 'Ish tajribalari'
        ordering = ['-boshlanish_sanasi']

    def __str__(self):
        return f"{self.kompaniya_nomi} - {self.lavozim}"



class Talim(models.Model):
    """Nomzodning ta'lim ma'lumotlari"""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='talim_malumotlari',
        verbose_name='Resume'
    )
    muassasa_nomi = models.CharField(
        max_length=200,
        verbose_name='Ta\'lim muassasasi nomi'
    )
    daraja = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Ta\'lim darajasi'
    )
    mutaxassislik = models.CharField(
        max_length=200,
        verbose_name='Mutaxassislik / Yo\'nalish'
    )
    boshlanish_yili = models.PositiveIntegerField(
        verbose_name='Boshlanish yili'
    )
    tugash_yili = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Tugash yili'
    )
    hozir_oqiyapman = models.BooleanField(
        default=False,
        verbose_name='Hozir o\'qiyapman'
    )
    gpa = models.DecimalField(
        max_digits=3, decimal_places=2,
        null=True, blank=True,
        verbose_name='GPA / O\'zlashtirish'
    )

    class Meta:
        verbose_name = 'Ta\'lim'
        verbose_name_plural = 'Ta\'lim ma\'lumotlari'
        ordering = ['-boshlanish_yili']

    def __str__(self):
        return f"{self.muassasa_nomi} - {self.get_daraja_display()}"



class Sertifikat(models.Model):
    """Nomzod sertifikatlari"""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='sertifikatlar',
        verbose_name='Resume'
    )
    nomi = models.CharField(
        max_length=200,
        verbose_name='Sertifikat nomi'
    )
    tashkilot = models.CharField(
        max_length=200,
        verbose_name='Bergan tashkilot'
    )
    berilgan_sana = models.DateField(
        verbose_name='Berilgan sana'
    )
    amal_qilish_muddati = models.DateField(
        null=True, blank=True,
        verbose_name='Amal qilish muddati'
    )
    muddatsiz = models.BooleanField(
        default=False,
        verbose_name='Muddatsiz'
    )
    sertifikat_id = models.CharField(
        max_length=100, blank=True,
        verbose_name='Sertifikat ID raqami'
    )
    havola = models.URLField(
        blank=True,
        verbose_name='Tasdiqlash havolasi'
    )

    class Meta:
        verbose_name = 'Sertifikat'
        verbose_name_plural = 'Sertifikatlar'
        ordering = ['-berilgan_sana']

    def __str__(self):
        return f"{self.nomi} - {self.tashkilot}"



class Maqola(models.Model):
    """Nomzod yozgan maqolalar"""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='maqolalar',
        verbose_name='Resume'
    )
    sarlavha = models.CharField(
        max_length=300,
        verbose_name='Maqola sarlavhasi'
    )
    nashriyot = models.CharField(
        max_length=200, blank=True,
        verbose_name='Nashriyot / Platforma'
    )
    nashr_sanasi = models.DateField(
        verbose_name='Nashr sanasi'
    )
    havola = models.URLField(
        blank=True,
        verbose_name='Maqola havolasi'
    )
    tavsif = models.TextField(
        blank=True,
        verbose_name='Qisqacha tavsif'
    )

    class Meta:
        verbose_name = 'Maqola'
        verbose_name_plural = 'Maqolalar'
        ordering = ['-nashr_sanasi']

    def __str__(self):
        return self.sarlavha



class Qiziqish(models.Model):
    """Nomzod qiziqishlari va hobbilar"""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='qiziqishlar',
        verbose_name='Resume'
    )
    nom = models.CharField(
        max_length=100,
        verbose_name='Qiziqish / Hobbi'
    )

    class Meta:
        verbose_name = 'Qiziqish'
        verbose_name_plural = 'Qiziqishlar'

    def __str__(self):
        return self.nom



class Yutuq(models.Model):
    """Nomzodning yutuq va mukofotlari"""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE,
        related_name='yutuqlar',
        verbose_name='Resume'
    )
    nomi = models.CharField(
        max_length=200,
        verbose_name='Yutuq nomi'
    )
    tashkilot = models.CharField(
        max_length=200, blank=True,
        verbose_name='Bergan tashkilot'
    )
    sana = models.DateField(
        null=True, blank=True,
        verbose_name='Sana'
    )
    tavsif = models.TextField(
        blank=True,
        verbose_name='Tavsif'
    )

    class Meta:
        verbose_name = 'Yutuq'
        verbose_name_plural = 'Yutuqlar'
        ordering = ['-sana']

    def __str__(self):
        return self.nomi
