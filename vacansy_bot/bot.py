"""
HR Mock Intervyu Platformasi — Telegram Bot
python-telegram-bot v20+ (PTB async)

Arxitektura:
  - ConversationHandler orqali ko'p bosqichli suhbat
  - Django ORM bilan sinc_to_async integratsiya
  - Kandidat va Tashkilot uchun alohida oqim
  - Platformaga bog'lash (token yoki login/parol)
  - Vakansiyalar yuborish (cron job)
  - HR vakansiya yaratish to'g'ridan-to'g'ri botdan
"""

import os
import secrets
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from asgiref.sync import sync_to_async
from django.utils import timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    BotCommand

)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    JobQueue,
)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Muhit o'zgaruvchilari ────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_2", "")
PLATFORM_URL = os.getenv("PLATFORM_URL", "http://127.0.0.1:8000").rstrip("/")
BOT_USERNAME = os.getenv("BOT_USERNAME", "hr_mock_bot")

# ─── ConversationHandler holatlari ───────────────────────────────────────────
(
    CHOOSE_ROLE,           # 0  Kandidat yoki HR tanlash
    AUTH_METHOD,           # 1  Login/parol yoki platforma bilan bog'lash
    ENTER_PHONE,           # 2  Telefon raqam (manual to'ldirish)
    ENTER_EMAIL,           # 3  Email (manual)
    ENTER_PASSWORD,        # 4  Parol
    CONFIRM_PROFILE,       # 5  Ma'lumotlarni tasdiqlash
    MANUAL_FIELD_CHOOSE,   # 6  Kandidat: qo'lda qaysi sohani tanlaydi
    WAITING_PLATFORM_LINK, # 7  Platform token havolasi kelishini kutish
    # HR uchun vakansiya yaratish bosqichlari
    VAC_TITLE,             # 8
    VAC_INDUSTRY,          # 9
    VAC_DESCRIPTION,       # 10
    VAC_SALARY,            # 11
    VAC_EMPLOYMENT,        # 12
    VAC_AI_INTERVIEW,      # 13
    VAC_CONFIRM,           # 14
    # Kandidat soha tasdiqlash
    CONFIRM_INDUSTRY,      # 15
    ENTER_INDUSTRY,        # 16
) = range(17)

# ─── Klaviatura tugmalari ─────────────────────────────────────────────────────
BTN_CANDIDATE = "👤 Ish izlayapman"
BTN_HR = "🏢 Ish beruvchiman"
BTN_LINK_PLATFORM = "🔗 Platforma bilan bog'lash"
BTN_LOGIN_PASS = "🔑 Login / Parol bilan kirish"
BTN_YES = "✅ Ha, to'g'ri"
BTN_NO = "❌ Yo'q, o'zgartiraman"
BTN_CANCEL = "🚫 Bekor qilish"
BTN_CREATE_VACANCY = "➕ Vakansiya yaratish"
BTN_MY_VACANCIES = "📋 Mening vakansiyalarim"
BTN_AI_INTERVIEW = "🤖 AI Intervyu"
BTN_SKIP = "⏭ O'tkazib yuborish"

# ─── Yordamchi DB funksiyalar ─────────────────────────────────────────────────

@sync_to_async
def get_user_by_chat_id(chat_id: str):
    from apps.users1.models import User
    return User.objects.filter(chat_id=chat_id).first()


@sync_to_async
def get_user_by_credentials(phone_or_email: str, password: str):
    """Login/parol bilan foydalanuvchi tekshirish"""
    from apps.users1.models import User
    from django.contrib.auth import authenticate

    user = None
    if "@" in phone_or_email:
        user = authenticate(email=phone_or_email.lower(), password=password)
    else:
        phone = phone_or_email if phone_or_email.startswith("+") else "+" + phone_or_email
        try:
            u = User.objects.get(phone_number=phone)
            if u.check_password(password):
                user = u
        except User.DoesNotExist:
            pass
    return user


@sync_to_async
def link_chat_id(user_id: int, chat_id: str):
    from apps.users1.models import User
    User.objects.filter(id=user_id).update(chat_id=chat_id)


@sync_to_async
def create_telegram_link_token(user_id: int) -> str:
    """Platformaga bog'lash uchun bir martalik token yaratish"""
    from apps.users1.models import TelegramLinkToken
    token = secrets.token_urlsafe(32)
    TelegramLinkToken.objects.create(
        user_id=user_id,
        token=token,
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    return token


@sync_to_async
def get_user_specialty(user) -> Optional[str]:
    """Kandidatning sohasini olish (resume yoki user_profile dan)"""
    try:
        # Resume modelidan industry ni olishga harakat
        resume = user.resumes.first()  # type: ignore[attr-defined]
        if resume and hasattr(resume, "industry"):
            return resume.industry
    except Exception:
        pass
    # user_type va boshqa ma'lumotlardan
    if hasattr(user, "industry"):
        return user.industry  # type: ignore[attr-defined]
    return None


@sync_to_async
def get_vacancies_for_user(user, limit: int = 5):
    """Foydalanuvchi sohasiga mos vakansiyalarni olish"""
    from apps.vacancies.models import Vacancy

    qs = Vacancy.objects.select_related("company").filter(
        publish_end__gte=timezone.now().date()
    )

    specialty = None
    try:
        from apps.resume.models import Resume
        resume = Resume.objects.filter(user=user).first()
        if resume and hasattr(resume, "mutaxassislik"):
            specialty = resume.mutaxassislik
    except Exception:
        pass

    if specialty:
        qs = qs.filter(industry__icontains=specialty)
    elif user.user_type == "candidate":
        pass  # barcha faol vakansiyalar

    return list(qs.order_by("-created_at")[:limit])


@sync_to_async
def create_vacancy_from_bot(hr_user, data: dict):
    """
    HR tomonidan botdan vakansiya yaratish.

    Agar CompanyProfile mavjud bo'lmasa — avtomatik yaratiladi.
    organization_name User modelidan olinadi (yoki data ichidagi sarlavha).
    """
    from apps.vacancies.models import Vacancy
    from apps.profile.models import CompanyProfile

    # get_or_create — CompanyProfile yo'q bo'lsa avtomatik yaratadi
    company_name = (
        hr_user.organization_name          # User modelida saqlangan
        or hr_user.get_full_name()
        or f"HR #{hr_user.id}"
    )
    company, created = CompanyProfile.objects.get_or_create(
        user=hr_user,
        defaults={
            "name": company_name,
            "industry": data.get("industry", ""),
        },
    )

    # Agar kompaniya endigina yaratilmagan bo'lsa, industry ni yangilash
    if not created and not company.industry and data.get("industry"):
        company.industry = data.get("industry", "")
        company.save(update_fields=["industry"])

    vacancy = Vacancy.objects.create(
        company=company,
        title=data.get("title", ""),
        industry=data.get("industry", ""),
        description=data.get("description", ""),
        salary_level=data.get("salary", "") or "Kelishuv bo'yicha",
        employment_type=data.get("employment_type", "FULL_TIME"),
        ai_improved_description=data.get("ai_interview_link", ""),
        publish_start=timezone.now().date(),
        publish_end=(timezone.now() + timedelta(days=30)).date(),
    )
    return vacancy, created   # (vacancy, kompaniya_yangi_yaratildimi)


@sync_to_async
def get_hr_vacancies(hr_user, limit: int = 10):
    from apps.profile.models import CompanyProfile

    company = CompanyProfile.objects.filter(user=hr_user).first()
    if not company:
        return []   # Profil yo'q — hali hech qanday vakansiya yo'q
    return list(company.vacancies.select_related("company").order_by("-created_at")[:limit])


@sync_to_async
def get_all_active_users_with_chat_id():
    from apps.users1.models import User
    return list(
        User.objects.filter(
            chat_id__isnull=False,
            is_active=True,
        ).exclude(chat_id="")
    )


# ─── Matn yordamchi funksiyalar ───────────────────────────────────────────────

def vacancy_card(v) -> str:
    """Vakansiya kartochkasi matnini yaratish"""
    salary = ""
    if v.salary_from and v.salary_to:
        salary = f"💰 {v.salary_from:,.0f} – {v.salary_to:,.0f} {v.currency or 'UZS'}"
    elif v.salary_level:
        salary = f"💰 {v.salary_level}"
    else:
        salary = "💰 Kelishuv bo'yicha"

    employment_map = {
        "FULL_TIME": "To'liq bandlik",
        "PART_TIME": "Qisman bandlik",
        "CONTRACT": "Shartnoma",
        "INTERNSHIP": "Amaliyot",
        "FREELANCE": "Frilans",
    }
    emp = employment_map.get(v.employment_type or "", v.employment_type or "")

    ai_line = ""
    if v.ai_improved_description and v.ai_improved_description.startswith("http"):
        ai_line = f"\n🤖 <a href='{v.ai_improved_description}'>AI Intervyu bo'limiga o'tish</a>"

    company_name = v.company.name if v.company else "Noma'lum kompaniya"

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏢 <b>{company_name}</b>\n"
        f"💼 <b>{v.title}</b>\n"
        f"📂 {v.industry or '—'}\n"
        f"{salary}\n"
        f"⏰ {emp}\n"
        f"📍 {v.region or 'Nomalum'}"
        f"{ai_line}\n"
        f"📅 <i>Muddati: {v.publish_end}</i>"
    )


def main_menu_keyboard(user_type: str) -> ReplyKeyboardMarkup:
    if user_type == "candidate":
        buttons = [
            [BTN_AI_INTERVIEW],
            [BTN_CANCEL],
        ]
    else:
        buttons = [
            [BTN_CREATE_VACANCY, BTN_MY_VACANCIES],
            [BTN_CANCEL],
        ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


# ─── /start buyrug'i ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Botga kirish nuqtasi"""
    context.user_data.clear()
    chat_id = str(update.effective_user.id)

    # Avval mavjud foydalanuvchi ekanligini tekshir
    user = await get_user_by_chat_id(chat_id)
    if user:
        context.user_data["user_id"] = user.id
        context.user_data["user_type"] = user.user_type

        name = user.get_full_name() or update.effective_user.first_name
        await update.message.reply_text(
            f"🎉 Xush kelibsiz, <b>{name}</b>!\n\n"
            f"Siz <b>{'Kandidat' if user.user_type == 'candidate' else 'HR / Tashkilot'}</b> sifatida kirgansiz.",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(user.user_type),
        )
        return ConversationHandler.END

    # Yangi foydalanuvchi
    keyboard = ReplyKeyboardMarkup(
        [[BTN_CANDIDATE], [BTN_HR]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "👋 <b>HR Mock Intervyu Platformasiga xush kelibsiz!</b>\n\n"
        "Siz kim sifatida kirasiz?",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return CHOOSE_ROLE


# ─── CHOOSE_ROLE ──────────────────────────────────────────────────────────────

async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == BTN_CANDIDATE:
        context.user_data["role"] = "candidate"
        role_label = "Kandidat (Ish izlayotgan)"
    elif text == BTN_HR:
        context.user_data["role"] = "organization"
        role_label = "HR / Tashkilot"
    else:
        await update.message.reply_text("Iltimos, quyidagi tugmalardan birini tanlang.")
        return CHOOSE_ROLE

    keyboard = ReplyKeyboardMarkup(
        [[BTN_LINK_PLATFORM], [BTN_LOGIN_PASS]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        f"✅ Siz <b>{role_label}</b> sifatida kiryapsiz.\n\n"
        "Platformaga qanday bog'lanmoqchisiz?\n\n"
        f"• <b>Platforma bilan bog'lash</b> — agar {PLATFORM_URL} da hisobingiz bo'lsa\n"
        "• <b>Login / Parol</b> — platforma login va parolingizni kiriting",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return AUTH_METHOD


# ─── AUTH_METHOD ─────────────────────────────────────────────────────────────

async def auth_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == BTN_LINK_PLATFORM:
        # Secure one-time token orqali bog'lash
        token = secrets.token_urlsafe(32)
        context.user_data["link_token"] = token
        context.user_data["tg_chat_id"] = str(update.effective_user.id)

        link_url = f"{PLATFORM_URL}/api/users/telegram/connect/?token={token}&chat_id={update.effective_user.id}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Platformaga kirish", url=link_url)],
            [InlineKeyboardButton("✅ Bog'landim, davom eting", callback_data="check_link")],
        ])
        await update.message.reply_text(
            "🔗 <b>Platformaga bog'lash</b>\n\n"
            "1. Quyidagi tugmani bosib platformaga kiring\n"
            "2. Profilingizda <b>«Telegramni ulash»</b> bo'limini toping\n"
            "3. Ulash tugmasini bosing\n"
            "4. Qaytib bu yerda <b>«Bog'landim»</b> tugmasini bosing\n\n"
            "⏳ Havola 15 daqiqa amal qiladi.",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
        return WAITING_PLATFORM_LINK

    elif text == BTN_LOGIN_PASS:
        await update.message.reply_text(
            "📱 Platformada ro'yxatdan o'tgan <b>email yoki telefon raqamingizni</b> kiriting:\n\n"
            "<i>Masalan: +998901234567 yoki user@example.com</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove(),
        )
        return ENTER_PHONE

    else:
        await update.message.reply_text("Iltimos, tugmalardan birini tanlang.")
        return AUTH_METHOD


# ─── WAITING_PLATFORM_LINK (callback) ────────────────────────────────────────

async def check_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    chat_id = str(query.from_user.id)
    user = await get_user_by_chat_id(chat_id)

    if not user:
        await query.edit_message_text(
            "⏳ Platformadan bog'lash hali amalga oshmagan.\n\n"
            "Iltimos avval platforma profilingizda 'Telegramni ulash' tugmasini bosing,\n"
            "keyin bu yerga qaytib 'Bog'landim' tugmasini bosing.",
        )
        return WAITING_PLATFORM_LINK

    context.user_data["user_id"] = user.id
    context.user_data["user_type"] = user.user_type

    await _show_profile_confirmation(query.message, user, edit=True)
    return CONFIRM_PROFILE


async def _show_profile_confirmation(message, user, edit: bool = False):
    role_label = "Kandidat" if user.user_type == "candidate" else "HR / Tashkilot"
    name = user.get_full_name()
    specialty = ""
    if user.user_type == "candidate":
        # Soha ma'lumoti
        specialty = f"\n📂 Soha: <b>{await get_user_specialty(user) or 'Korsatilmagan'}</b>"

    org_info = ""
    if user.user_type == "organization":
        org_info = (
            f"\n🏢 Tashkilot: <b>{user.organization_name or '—'}</b>"
            f"\n💼 Lavozim: <b>{user.position or '—'}</b>"
        )

    text = (
        f"✅ <b>Ma'lumotlaringiz topildi!</b>\n\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"🎭 Rol: <b>{role_label}</b>"
        f"{specialty}"
        f"{org_info}\n\n"
        "Bu ma'lumotlar to'g'rimi?"
    )
    keyboard = ReplyKeyboardMarkup(
        [[BTN_YES], [BTN_NO]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    if edit:
        await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# ─── ENTER_PHONE (login/parol oqimi) ─────────────────────────────────────────

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone_or_email = update.message.text.strip()
    context.user_data["login"] = phone_or_email

    await update.message.reply_text(
        "🔐 Platformadagi <b>parolingizni</b> kiriting:",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove(),
    )
    return ENTER_PASSWORD


# ─── ENTER_PASSWORD ───────────────────────────────────────────────────────────

async def enter_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text.strip()
    login = context.user_data.get("login", "")
    chat_id = str(update.effective_user.id)

    # Xabarni darhol o'chirish (xavfsizlik)
    try:
        await update.message.delete()
    except Exception:
        pass

    msg = await update.message.reply_text("⏳ Tekshirilmoqda...")

    user = await get_user_by_credentials(login, password)

    if not user:
        await msg.edit_text(
            "❌ <b>Login yoki parol noto'g'ri!</b>\n\n"
            "Iltimos platformadagi ma'lumotlaringizni tekshirib qaytadan kiriting.\n"
            "Email yoki telefon raqamingizni yuboring:",
            parse_mode=ParseMode.HTML,
        )
        return ENTER_PHONE

    # chat_id ni saqlash
    await link_chat_id(user.id, chat_id)
    context.user_data["user_id"] = user.id
    context.user_data["user_type"] = user.user_type

    await msg.delete()
    await _show_profile_confirmation(update.message, user)
    return CONFIRM_PROFILE


# ─── CONFIRM_PROFILE ──────────────────────────────────────────────────────────

async def confirm_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_type = context.user_data.get("user_type", "candidate")

    if text == BTN_YES:
        if user_type == "candidate":
            return await _candidate_confirmed(update, context)
        else:
            return await _hr_confirmed(update, context)

    elif text == BTN_NO:
        # Soha/tashkilotni qaytadan kiritish
        if user_type == "candidate":
            await update.message.reply_text(
                "📂 Qaysi sohada ish izlayapsiz? Yozing:\n"
                "<i>Masalan: Data Analytics, Frontend, Marketing...</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove(),
            )
            return ENTER_INDUSTRY
        else:
            await update.message.reply_text(
                "✏️ Tashkilotingiz va lavozimingizni qaytadan kiriting:\n"
                "<i>Masalan: TechCorp — HR Manager</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove(),
            )
            return ENTER_INDUSTRY
    else:
        await update.message.reply_text("Iltimos, tugmalardan birini bosing.")
        return CONFIRM_PROFILE


async def _candidate_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kandidat tasdiqladi — asosiy menyuga o'tish"""
    await update.message.reply_text(
        "🎉 <b>Muvaffaqiyatli kirdingiz!</b>\n\n"
        "Sohangizga mos yangi vakansiyalar avtomatik yuborib boriladi.\n"
        "AI intervyu bo'lgan vakansiyalarda to'g'ridan-to'g'ri o'tish imkoni ham bo'ladi! 🤖",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard("candidate"),
    )
    return ConversationHandler.END


async def _hr_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """HR tasdiqladi — HR menyuga o'tish"""
    await update.message.reply_text(
        "🎉 <b>Xush kelibsiz, HR!</b>\n\n"
        "Siz platformadagi barcha vakansiyalaringizni bu yerdan ham boshqarishingiz mumkin.\n"
        "Botdan to'g'ridan-to'g'ri vakansiya yaratishingiz, AI intervyu qo'shishingiz mumkin! 🚀",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard("organization"),
    )
    return ConversationHandler.END


# ─── ENTER_INDUSTRY (soha qaytadan kiritish) ──────────────────────────────────

async def enter_industry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    industry = update.message.text.strip()
    user_id = context.user_data.get("user_id")
    user_type = context.user_data.get("user_type", "candidate")

    if user_id:
        from apps.users1.models import User

        @sync_to_async
        def _update_industry():
            user = User.objects.filter(id=user_id).first()
            if user and user_type == "candidate":
                # Resume yoki boshqa model orqali saqlash
                try:
                    from apps.resume.models import Resume
                    resume = Resume.objects.filter(user=user).first()
                    if resume and hasattr(resume, "mutaxassislik"):
                        resume.mutaxassislik = industry
                        resume.save(update_fields=["mutaxassislik"])
                except Exception:
                    pass
            elif user and user_type == "organization":
                parts = industry.split("—")
                if len(parts) == 2:
                    user.organization_name = parts[0].strip()
                    user.position = parts[1].strip()
                    user.save(update_fields=["organization_name", "position"])

        await _update_industry()

    await update.message.reply_text(
        f"✅ Yangilandi: <b>{industry}</b>",
        parse_mode=ParseMode.HTML,
    )

    if user_type == "candidate":
        return await _candidate_confirmed(update, context)
    else:
        return await _hr_confirmed(update, context)


# ─── HR VAKANSIYA YARATISH oqimi ─────────────────────────────────────────────

async def cmd_create_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """HR dan vakansiya yaratishni boshlash"""
    chat_id = str(update.effective_user.id)
    user = await get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_text(
            "⚠️ Siz hali botga kirgansiz.\n"
            "Iltimos /start bosing va HR sifatida kiring.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    if user.user_type != "organization":
        await update.message.reply_text(
            "⛔ Bu funksiya faqat HR / Tashkilot foydalanuvchilari uchun.\n"
            "Iltimos /start orqali HR sifatida kiring."
        )
        return ConversationHandler.END

    # user_id ni har doim yangilab qo'yamiz
    context.user_data["user_id"] = user.id
    context.user_data["user_type"] = user.user_type
    context.user_data["vac"] = {}

    await update.message.reply_text(
        "➕ <b>Yangi vakansiya yaratish</b>\n\n"
        "📌 Vakansiya sarlavhasini kiriting:\n"
        "<i>Masalan: Senior Python Developer</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove(),
    )
    return VAC_TITLE


async def vac_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vac"]["title"] = update.message.text.strip()
    await update.message.reply_text(
        "📂 <b>Sohani kiriting:</b>\n"
        "<i>Masalan: IT / Dasturlash, Marketing, Moliya...</i>",
        parse_mode=ParseMode.HTML,
    )
    return VAC_INDUSTRY


async def vac_industry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vac"]["industry"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 <b>Vakansiya tavsifini kiriting:</b>\n"
        "<i>Vazifalar, talablar, imtiyozlar...</i>",
        parse_mode=ParseMode.HTML,
    )
    return VAC_DESCRIPTION


async def vac_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vac"]["description"] = update.message.text.strip()
    keyboard = ReplyKeyboardMarkup(
        [["Kelishuv bo'yicha"], [BTN_SKIP]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "💰 <b>Maosh darajasini kiriting:</b>\n"
        "<i>Masalan: 3,000,000 – 5,000,000 UZS yoki «Kelishuv bo'yicha»</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return VAC_SALARY


async def vac_salary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["vac"]["salary"] = "" if text == BTN_SKIP else text

    keyboard = ReplyKeyboardMarkup(
        [
            ["To'liq bandlik", "Qisman bandlik"],
            ["Shartnoma", "Amaliyot", "Frilans"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "⏰ <b>Bandlik turini tanlang:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return VAC_EMPLOYMENT


async def vac_employment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    emp_map = {
        "To'liq bandlik": "FULL_TIME",
        "Qisman bandlik": "PART_TIME",
        "Shartnoma": "CONTRACT",
        "Amaliyot": "INTERNSHIP",
        "Frilans": "FREELANCE",
    }
    raw = update.message.text.strip()
    context.user_data["vac"]["employment_type"] = emp_map.get(raw, "FULL_TIME")

    keyboard = ReplyKeyboardMarkup(
        [["✅ Ha, AI intervyu qo'shaman"], ["⏭ Yo'q, o'tkazib yuboraman"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "🤖 <b>AI Intervyu bo'limini qo'shmoqchimisiz?</b>\n\n"
        "Agar «Ha» desangiz, platformadagi AI intervyu havolasi vakansiyaga qo'shiladi.\n"
        "Nomzodlar to'g'ridan-to'g'ri AI intervyuga o'ta oladilar.",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return VAC_AI_INTERVIEW


async def vac_ai_interview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if "Ha" in text:
        # AI intervyu havolasini platformadan olish
        user_id = context.user_data.get("user_id")
        ai_link = f"{PLATFORM_URL}/swagger/#/AI%20Interview"
        context.user_data["vac"]["ai_interview_link"] = ai_link
        ai_info = f"🔗 AI intervyu havolasi: {ai_link}"
    else:
        context.user_data["vac"]["ai_interview_link"] = ""
        ai_info = "AI intervyu qo'shilmaydi."

    vac = context.user_data["vac"]
    preview = (
        "📋 <b>Vakansiya ko'rgazmasi:</b>\n\n"
        f"💼 Sarlavha: <b>{vac.get('title', '—')}</b>\n"
        f"📂 Soha: <b>{vac.get('industry', '—')}</b>\n"
        f"📝 Tavsif: {vac.get('description', '—')[:200]}...\n"
        f"💰 Maosh: {vac.get('salary', 'Kelishuv') or 'Kelishuv boyicha'}\n"
        f"⏰ Bandlik: {vac.get('employment_type', 'FULL_TIME')}\n"
        f"{ai_info}\n\n"
        "✅ Joylashtirilsinmi?"
    )
    keyboard = ReplyKeyboardMarkup(
        [[BTN_YES], [BTN_NO]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(preview, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    return VAC_CONFIRM


async def vac_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == BTN_YES:
        user_id = context.user_data.get("user_id")
        if not user_id:
            await update.message.reply_text(
                "❌ Sessiya muddati tugadi. Qaytadan /create_vacancy bosing.",
                reply_markup=main_menu_keyboard("organization"),
            )
            return ConversationHandler.END

        @sync_to_async
        def _get_user():
            from apps.users1.models import User
            return User.objects.filter(id=user_id).first()

        hr_user = await _get_user()
        if not hr_user:
            await update.message.reply_text(
                "❌ Foydalanuvchi topilmadi. /start bosing.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        try:
            result = await create_vacancy_from_bot(hr_user, context.user_data["vac"])
            vacancy, company_created = result
        except Exception as e:
            logger.error(f"Vakansiya yaratishda xato: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Xatolik yuz berdi: {e}\n\nQaytadan urinib ko'ring: /create_vacancy",
                reply_markup=main_menu_keyboard("organization"),
            )
            return ConversationHandler.END

        new_company_note = (
            "\n\n⚠️ <i>Kompaniya profili avtomatik yaratildi. "
            f"To'ldirib qo'yish uchun: {PLATFORM_URL}/api/profile/company-profile/me/ (PATCH)</i>"
            if company_created else ""
        )

        if vacancy:
            await update.message.reply_text(
                f"🎉 <b>Vakansiya muvaffaqiyatli joylashtirildi!</b>\n\n"
                f"ID: #{vacancy.id}\n"
                f"💼 {vacancy.title}\n\n"
                f"Vakansiya platformadagi dashboardingizda ham ko'rinadi.\n"
                f"🔗 {PLATFORM_URL}/api/profile/company-vacancies/"
                f"{new_company_note}",
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard("organization"),
            )
        else:
            await update.message.reply_text(
                "❌ Kutilmagan xatolik yuz berdi. Qaytadan urinib ko'ring.\n"
                "/create_vacancy",
                reply_markup=main_menu_keyboard("organization"),
            )

    else:
        await update.message.reply_text(
            "❌ Vakansiya bekor qilindi.",
            reply_markup=main_menu_keyboard("organization"),
        )

    context.user_data.pop("vac", None)
    return ConversationHandler.END


# ─── HR vakansiyalarini ko'rish ───────────────────────────────────────────────

async def cmd_my_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_user.id)
    user = await get_user_by_chat_id(chat_id)

    if not user or user.user_type != "organization":
        await update.message.reply_text("⛔ Faqat HR uchun.")
        return ConversationHandler.END

    vacancies = await get_hr_vacancies(user)
    if not vacancies:
        await update.message.reply_text(
            "📋 Hozircha vakansiyalaringiz yo'q.\n"
            "Yangi vakansiya yaratish uchun «➕ Vakansiya yaratish» tugmasini bosing.",
            reply_markup=main_menu_keyboard("organization"),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"📋 <b>Sizning vakansiyalaringiz ({len(vacancies)} ta):</b>",
        parse_mode=ParseMode.HTML,
    )
    for v in vacancies:
        card = vacancy_card(v)
        await update.message.reply_text(card, parse_mode=ParseMode.HTML)

    return ConversationHandler.END


# ─── AI Intervyu (kandid uchun) ───────────────────────────────────────────────

async def cmd_ai_interview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_user.id)
    user = await get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_text("Iltimos avval /start orqali kiring.")
        return ConversationHandler.END

    # AI intervyu havolasi — Swagger orqali yoki frontendingiz bo'lsa shu URL ni almashtiring
    ai_url = f"{PLATFORM_URL}/swagger/#/AI%20Interview%20Questions"
    swagger_url = f"{PLATFORM_URL}/swagger/"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 AI Intervyu savollarini ko'rish", url=swagger_url)],
    ])
    await update.message.reply_text(
        "🤖 <b>AI Mock Intervyu</b>\n\n"
        "Platforma orqali AI intervyuga kirish:\n"
        f"🔗 {swagger_url}\n\n"
        "<i>Swagger sahifasida AI Interview Questions bo'limini oching,</i>\n"
        "<i>so'ng \'Authorize\' tugmasini bosib JWT tokeningizni kiriting.</i>\n\n"
        "📌 <b>Frontendingiz tayyor bo'lgach, bu URL ni yangilang:</b>\n"
        "<code>PLATFORM_URL/ai-interview/</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return ConversationHandler.END


# ─── Vakansiyalarni ko'rish (kandidat uchun) ──────────────────────────────────

async def cmd_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_user.id)
    user = await get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_text("Iltimos avval /start orqali kiring.")
        return ConversationHandler.END

    if user.user_type != "candidate":
        await update.message.reply_text("Bu buyruq faqat kandidatlar uchun.")
        return ConversationHandler.END

    await update.message.reply_text("🔍 Sohangizga mos vakansiyalar izlanmoqda...")

    vacancies = await get_vacancies_for_user(user)
    if not vacancies:
        await update.message.reply_text(
            "😔 Hozircha sohangizga mos aktiv vakansiyalar topilmadi.\n"
            "Yangi vakansiyalar qo'shilganda avtomatik xabar beriladi!",
            reply_markup=main_menu_keyboard("candidate"),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"✅ <b>{len(vacancies)} ta vakansiya topildi:</b>",
        parse_mode=ParseMode.HTML,
    )
    for v in vacancies:
        card = vacancy_card(v)
        await update.message.reply_text(card, parse_mode=ParseMode.HTML)

    return ConversationHandler.END


# ─── Bekor qilish ─────────────────────────────────────────────────────────────

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_user.id)
    user = await get_user_by_chat_id(chat_id)

    context.user_data.clear()

    if user:
        await update.message.reply_text(
            "✅ Amal bekor qilindi.",
            reply_markup=main_menu_keyboard(user.user_type or "candidate"),
        )
    else:
        await update.message.reply_text(
            "✅ Amal bekor qilindi. /start bosing.",
            reply_markup=ReplyKeyboardRemove(),
        )
    return ConversationHandler.END


# ─── Noaniq xabar ─────────────────────────────────────────────────────────────

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_user.id)
    user = await get_user_by_chat_id(chat_id)

    if user:
        await update.message.reply_text(
            "❓ Tushunmadim. Quyidagi menyudan foydalaning:",
            reply_markup=main_menu_keyboard(user.user_type or "candidate"),
        )
    else:
        await update.message.reply_text(
            "❓ Botdan foydalanish uchun /start bosing."
        )


# ─── CRON JOB: vakansiyalarni yuborish ────────────────────────────────────────

async def send_vacancies_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Har kuni yangi vakansiyalarni tegishli foydalanuvchilarga yuborish.
    JobQueue orqali ishga tushiriladi.
    """
    logger.info("📤 Vakansiyalar yuborish job boshlandi")

    users = await get_all_active_users_with_chat_id()
    sent_count = 0

    for user in users:
        if user.user_type != "candidate":
            continue
        if not user.chat_id:
            continue

        try:
            vacancies = await get_vacancies_for_user(user, limit=3)
            if not vacancies:
                continue

            await context.bot.send_message(
                chat_id=user.chat_id,
                text=(
                    f"🔔 <b>Yangi vakansiyalar!</b>\n"
                    f"Sohangizga mos <b>{len(vacancies)} ta</b> yangi vakansiya:\n"
                ),
                parse_mode=ParseMode.HTML,
            )

            for v in vacancies:
                card = vacancy_card(v)
                await context.bot.send_message(
                    chat_id=user.chat_id,
                    text=card,
                    parse_mode=ParseMode.HTML,
                )
                await asyncio.sleep(0.3)

            sent_count += 1

        except Exception as e:
            logger.warning(f"Foydalanuvchi {user.chat_id} ga yuborishda xato: {e}")

    logger.info(f"✅ Vakansiyalar {sent_count} ta foydalanuvchiga yuborildi")


# ─── Xato handler ─────────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Xato yuz berdi: {context.error}", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.\n"
                "Muammo davom etsa /start bosing."
            )
        except Exception:
            pass


# ─── Botni yig'ish va ishga tushirish ────────────────────────────────────────

def build_conversation_handler() -> ConversationHandler:
    """Asosiy ConversationHandler — barcha oqimlarni birlashtiradi"""

    # Vakansiya yaratish uchun entry point
    vac_entry = MessageHandler(filters.Regex(f"^{BTN_CREATE_VACANCY}$"), cmd_create_vacancy)

    # Mening vakansiyalarim
    my_vac_entry = MessageHandler(filters.Regex(f"^{BTN_MY_VACANCIES}$"), cmd_my_vacancies)

    return ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            CommandHandler("create_vacancy", cmd_create_vacancy),
            MessageHandler(filters.Regex(f"^{BTN_CREATE_VACANCY}$"), cmd_create_vacancy),
        ],
        states={
            CHOOSE_ROLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_role)
            ],
            AUTH_METHOD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, auth_method)
            ],
            WAITING_PLATFORM_LINK: [
                CallbackQueryHandler(check_link_callback, pattern="^check_link$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: WAITING_PLATFORM_LINK),
            ],
            ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)
            ],
            ENTER_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password)
            ],
            CONFIRM_PROFILE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_profile)
            ],
            ENTER_INDUSTRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_industry)
            ],
            VAC_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vac_title)
            ],
            VAC_INDUSTRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vac_industry)
            ],
            VAC_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vac_description)
            ],
            VAC_SALARY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vac_salary)
            ],
            VAC_EMPLOYMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vac_employment)
            ],
            VAC_AI_INTERVIEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vac_ai_interview)
            ],
            VAC_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vac_confirm)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            MessageHandler(filters.Regex(f"^{BTN_CANCEL}$"), cmd_cancel),
        ],
        allow_reentry=True,
        name="main_conv",
        persistent=False,
    )


async def post_init(application):
    """Bot ishga tushganda komandalar menyusini o'rnatadi"""
    commands = [
        BotCommand("start", "Botni qayta ishga tushirish"),
        BotCommand("vacancies", "Mos vakansiyalarni ko'rish"),
        BotCommand("ai_interview", "AI Mock Intervyuni boshlash"),
        BotCommand("create_vacancy", "Yangi vakansiya yaratish (HR)"),
        BotCommand("my_vacancies", "Mening vakansiyalarim (HR)"),
        BotCommand("cancel", "Amalni bekor qilish"),
    ]
    await application.bot.set_my_commands(commands)



def run_bot():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN_2 muhit o'zgaruvchisi topilmadi!")

    logger.info(f"🤖 HR Bot ishga tushmoqda... (@{BOT_USERNAME})")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Asosiy conversation handler
    app.add_handler(build_conversation_handler())

    # Alohida command handlerlar (conversation tashqarisida ham ishlaydi)
    app.add_handler(CommandHandler("vacancies", cmd_vacancies))
    app.add_handler(CommandHandler("ai_interview", cmd_ai_interview))
    app.add_handler(CommandHandler("my_vacancies", cmd_my_vacancies))

    # Menyudan bosish uchun MessageHandlerlar
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_MY_VACANCIES}$"), cmd_my_vacancies))
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_AI_INTERVIEW}$"), cmd_ai_interview))

    # Noaniq xabarlar
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    # Xato handler
    app.add_error_handler(error_handler)

    # Cron job — har kuni ertalab 09:00 da vakansiyalar yuborish
    app.job_queue.run_daily(
        send_vacancies_job,
        time=datetime.strptime("09:00", "%H:%M").time().replace(tzinfo=timezone.get_current_timezone()),
        name="daily_vacancies",
    )

    # Har 6 soatda ham yuborish imkoniyati
    app.job_queue.run_repeating(
        send_vacancies_job,
        interval=timedelta(hours=6),
        first=timedelta(minutes=5),  # ishga tushgandan 5 daqiqa keyin
        name="repeating_vacancies",
    )

    logger.info("✅ Bot muvaffaqiyatli ishga tushdi. Polling boshlandi...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    run_bot()