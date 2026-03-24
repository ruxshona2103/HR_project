from django.db import models


class Vacancy(models.Model):
    TYPE_CHOICES = [
        ("system", "System"),
        ("national", "National"),
        ("international", "International"),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ("FULL_TIME", "To'liq bandlik"),
        ("PART_TIME", "Qisman bandlik"),
        ("CONTRACT", "Shartnoma asosida"),
        ("INTERNSHIP", "Amaliyot"),
        ("FREELANCE", "Frilans"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("NO_EXPERIENCE", "Tajribasiz"),
        ("UP_TO_1", "1 yilgacha"),
        ("ONE_TO_THREE", "1-3 yil"),
        ("THREE_TO_FIVE", "3-5 yil"),
        ("FIVE_PLUS", "5+ yil"),
    ]

    EDUCATION_LEVEL_CHOICES = [
        ("NOT_REQUIRED", "Muhim emas"),
        ("SECONDARY", "O'rta"),
        ("SECONDARY_SPECIAL", "O'rta maxsus"),
        ("BACHELOR", "Bakalavr"),
        ("MASTER", "Magistr"),
        ("PHD", "PhD"),
    ]

    WORK_SCHEDULE_CHOICES = [
        ("6_1", "6/1"),
        ("5_2", "5/2"),
        ("4_4", "4/4"),
        ("4_2", "4/2"),
        ("3_2", "3/2"),
        ("2_2", "2/2"),
        ("2_1", "2/1"),
        ("WEEKENDS", "Dam olish kunlarida"),
        ("FLEXIBLE", "Erkin"),
        ("OTHER", "Boshqa"),
    ]

    DAILY_HOURS_CHOICES = [
        ("2", "2"),
        ("4", "4"),
        ("6", "6"),
        ("8", "8"),
        ("10", "10"),
        ("12", "12"),
        ("24", "24"),
        ("BY_AGREEMENT", "Kelishuv bo'yicha"),
        ("OTHER", "Boshqa"),
    ]

    CURRENCY_CHOICES = [
        ("UZS", "UZS"),
        ("USD", "USD"),
        ("EUR", "EUR"),
        ("RUB", "RUB"),
    ]

    WORK_FORMAT_CHOICES = [
        ("OFFICE", "Ofis"),
        ("REMOTE", "Masofadan"),
        ("HYBRID", "Gibrid"),
        ("FIELD", "Joylarga chiqish shaklida"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Vakansiya tavsifi, vazifalar va talablar")

    # Asosiy ma'lumotlar
    photo = models.ImageField(
        upload_to="vacancies/photos/", null=True, blank=True
    )
    industry = models.CharField(
        max_length=255,
        help_text="Kasb sohasi",
    )
    specialization = models.CharField(
        max_length=255,
        help_text="Kasb yo'nalishi",
    )
    vacant_slots = models.PositiveIntegerField(
        default=1, help_text="Vakant o'rinlari soni"
    )
    required_skills = models.TextField(
        help_text="Kerakli ko'nikmalar (vergul bilan ajratib yozing)"
    )

    # Maosh va talablar
    salary_level = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Maosh darajasi (ixtiyoriy matn)",
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        null=True,
        blank=True,
    )
    salary_from = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimal maosh",
    )
    salary_to = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maksimal maosh",
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
    )

    # Hudud va ish turi
    region = models.CharField(
        max_length=255,
        help_text="Viloyat",
    )
    district = models.CharField(
        max_length=255,
        help_text="Tuman / Shahar",
    )
    work_formats = models.JSONField(
        default=list,
        blank=True,
        help_text="Ish turi (bir nechta qiymat: OFfICE/REMOTE/HYBRID/FIELD)",
    )
    work_schedule = models.CharField(
        max_length=20,
        choices=WORK_SCHEDULE_CHOICES,
    )
    daily_hours = models.CharField(
        max_length=20,
        choices=DAILY_HOURS_CHOICES,
    )
    company_address = models.TextField(
        help_text="Korxona manzili (matn ko'rinishida)",
    )
    map_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    map_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    # Muddat va izoh
    publish_start = models.DateField()
    publish_end = models.DateField()
    ai_improved_description = models.TextField(
        null=True,
        blank=True,
        help_text="AI tomonidan takomillashtirilgan tavsif (ixtiyoriy)",
    )

    # Mavjud maydonlarni moslik uchun qoldiramiz
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="system")
    min_experience = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class Candidate(models.Model):
    name = models.CharField(max_length=100)
    skills = models.TextField(
        help_text="Nomzod ko'nikmalari (vergul bilan ajratib yozing)"
    )
    experience = models.IntegerField(help_text="Tajriba yillarda")

    def __str__(self) -> str:
        return self.name