import os
import random
import django
from django.utils import timezone
from dotenv import load_dotenv

load_dotenv()

"""Django sozlamalarini yuklash — bot alohida ishlaydi shuning uchun"""
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asgiref.sync import sync_to_async
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from apps.users1.models import OTPCode, User, PendingRegistration
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telefon raqam so'rash tugmasi"""
    if not update.message:
        return
    button = KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Assalomu alaykum! Ro'yxatdan o'tish uchun telefon raqamingizni yuboring.",
        reply_markup=keyboard
    )


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telefon raqam kelganda — Login yoki Register uchun OTP yuborish"""
    contact = update.message.contact
    tg_user = update.message.from_user

    phone = contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone

    chat_id = str(tg_user.id)

    # User mavjudmi yoki PendingRegistration bormi tekshirish
    user_exists = await sync_to_async(
        User.objects.filter(phone_number=phone).exists
    )()

    pending_exists = await sync_to_async(
        PendingRegistration.objects.filter(phone_number=phone).exists
    )()

    # Agar ikkalasi ham yo'q — web saytda avval ro'yxatdan o'tish kerak deb aytadi
    if not user_exists and not pending_exists:
        await update.message.reply_text(
            "⚠️ Bu telefon raqam ro'yxatdan o'tmagan.\n\n"
            "Iltimos avval web saytda ro'yxatdan o'ting.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    #  Agar faol kod allaqachon bor bo'lsa — yangi kod bermaslik
    existing_otp = await sync_to_async(
        lambda: OTPCode.objects.filter(
            phone_number=phone,
            is_used=False
        ).order_by('-created_at').first()
    )()

    if existing_otp and not existing_otp.is_expired():
        remaining = max(0, int(300 - (timezone.now() - existing_otp.created_at).total_seconds()))
        await update.message.reply_text(
            f"⏳ Eski kodingiz hali ham amal qiladi. {remaining} soniya kuting.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Eski kodlarni o'chirish
    await sync_to_async(
        OTPCode.objects.filter(phone_number=phone, is_used=False).delete
    )()

    # Yangi kod yaratish
    code = str(random.randint(100000, 999999))

    await sync_to_async(OTPCode.objects.create)(
        phone_number=phone,
        chat_id=chat_id,
        code=code
    )

    await update.message.reply_text(
        f"✅ Sizning tasdiqlash kodingiz:\n\n"
        f"`{code}`\n\n"
        f"Kodni web saytga kiriting. Kod 5 daqiqada eskiradi.\n\n"
        f"Yangi kod olish uchun /start ni bosing.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/login buyrug'i — mavjud user uchun yangi kod yuborish"""
    if not update.message:
        return

    chat_id = str(update.message.from_user.id)

    user_exists = await sync_to_async(
        User.objects.filter(chat_id=chat_id).exists
    )()

    if not user_exists:
        await update.message.reply_text(
            "Siz hali ro'yxatdan o'tmagansiz. /start bosing."
        )
        return

    user = await sync_to_async(User.objects.get)(chat_id=chat_id)

    # Faol kod bormi tekshirish
    existing_otp = await sync_to_async(
        lambda: OTPCode.objects.filter(
            phone_number=user.phone_number,
            is_used=False
        ).order_by('-created_at').first()
    )()

    if existing_otp and not existing_otp.is_expired():
        remaining = max(0, int(300 - (timezone.now() - existing_otp.created_at).total_seconds()))
        await update.message.reply_text(
            f"⏳ Eski kodingiz hali ham amal qiladi. {remaining} soniya kuting."
        )
        return

    # Eski kodlarni o'chirish
    await sync_to_async(
        OTPCode.objects.filter(phone_number=user.phone_number, is_used=False).delete
    )()

    code = str(random.randint(100000, 999999))

    await sync_to_async(OTPCode.objects.create)(
        phone_number=user.phone_number,
        chat_id=chat_id,
        code=code
    )

    sent_message = await update.message.reply_text(
        f"🔐 Sizning login kodingiz:\n\n"
        f"`{code}`\n\n"
        f"Kod 5 daqiqada eskiradi.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Yangi kod", callback_data=f"renew_{user.phone_number}")
        ]])
    )

    context.job_queue.run_once(
        expire_code_message,
        300,
        data={
            'chat_id': chat_id,
            'message_id': sent_message.message_id,
            'phone': user.phone_number
        }
    )


async def renew_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'Yangi kod' tugmasi bosilganda"""
    query = update.callback_query

    phone = query.data.replace("renew_", "")
    chat_id = str(query.from_user.id)

    existing_otp = await sync_to_async(
        lambda: OTPCode.objects.filter(
            phone_number=phone,
            is_used=False
        ).order_by('-created_at').first()
    )()

    if existing_otp and not existing_otp.is_expired():
        remaining = max(0, int(300 - (timezone.now() - existing_otp.created_at).total_seconds()))
        await query.answer(
            text=f"⏳ Eski kod hali amal qiladi. {remaining} soniya kuting.",
            show_alert=True
        )
        return

    await query.answer()

    await sync_to_async(
        OTPCode.objects.filter(phone_number=phone, is_used=False).delete
    )()

    code = str(random.randint(100000, 999999))

    await sync_to_async(OTPCode.objects.create)(
        phone_number=phone,
        chat_id=chat_id,
        code=code
    )

    sent_message = await query.edit_message_text(
        f"🔐 Yangi login kodingiz:\n\n"
        f"`{code}`\n\n"
        f"Kod 5 daqiqada eskiradi.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Yangi kod", callback_data=f"renew_{phone}")
        ]])
    )

    context.job_queue.run_once(
        expire_code_message,
        300,
        data={
            'chat_id': chat_id,
            'message_id': sent_message.message_id,
            'phone': phone
        }
    )


async def expire_code_message(context: ContextTypes.DEFAULT_TYPE):
    """5 daqiqadan keyin xabarni eskirgan deb belgilash"""
    data = context.job.data
    try:
        await context.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text="🔒 Kod muddati tugadi. Yangi kod olish uchun <b>Yangi kod</b> tugmasini bosing.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Yangi kod", callback_data=f"renew_{data['phone']}")
            ]])
        )
    except Exception:
        pass


async def error_handler(update, context):
    print(f"Xato: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "Xatolik yuz berdi. Qaytadan urinib ko'ring."
        )


def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(CallbackQueryHandler(renew_handler, pattern="^renew_"))
    app.add_error_handler(error_handler)
    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == '__main__':
    run_bot()
