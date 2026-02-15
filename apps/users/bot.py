import os
import random
import django
from django.utils import timezone
from dotenv import load_dotenv

load_dotenv()

"""Django sozlamalarini yuklash — bot alohida ishlaydi shuning uchun """
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asgiref.sync import sync_to_async
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from apps.users.models import OTPCode, User
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
    contact = update.message.contact
    user = update.message.from_user

    phone = contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone

    chat_id = str(user.id)
    username = user.username or ''

    """Xali eskirmagan ushlatilmagan kod bormi yo'zmi tekshiradi"""
    existing_otp = await sync_to_async(
        lambda: OTPCode.objects.filter(
            phone_number=phone,
            is_used=False
        ).order_by('-created_at').first()
    )()

    if existing_otp and not existing_otp.is_expired():
        remaining = max(0, int(60 - (timezone.now() - existing_otp.created_at).total_seconds()))
        await update.message.reply_text(
            f"Eski kodingiz hali ham amal qiladi. "
            f"{remaining} soniya kuting.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    """ Eski kodlarni o'chiradi"""
    await sync_to_async(
        OTPCode.objects.filter(phone_number=phone, is_used=False).delete
    )()

    code = str(random.randint(100000, 999999))

    await sync_to_async(OTPCode.objects.create)(
        phone_number=phone,
        chat_id=chat_id,
        username=username,
        code=code
    )

    await update.message.reply_text(
        f"✅ Sizning tasdiqlash kodingiz:\n\n"
        f"`{code}`\n\n"
        f"Kodni web saytga kiriting. Kod 60 soniyada eskiradi.\n\n"
        f"🔑 Yangi kod olish uchun /login ni bosing",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = str(update.message.from_user.id)

    user_exists = await sync_to_async(
        User.objects.filter(chat_id=chat_id).exists
    )()

    if not user_exists:
        await update.message.reply_text(
            f"Siz hali ro'yxatdan o'tmagansiz. /start bosing."
        )
        return

    user = await sync_to_async(User.objects.get)(chat_id=chat_id)

    """Xali eskirmagan ushlatilmagan kod bormi yo'zmi tekshiradi"""
    existing_otp = await sync_to_async(
        lambda: OTPCode.objects.filter(
            phone_number=user.phone_number,
            is_used=False
        ).order_by('-created_at').first()
    )()



    if existing_otp and not existing_otp.is_expired():
        remaining = max(0, int(60 - (timezone.now() - existing_otp.created_at).total_seconds()))
        await update.message.reply_text(
            f"Eski kodingiz hali ham amal qiladi, iltimos uni ishlating yoki {remaining} soniya kuting."
        )
        return

    """Eski kodlarni o'chirish"""
    await sync_to_async(
        OTPCode.objects.filter(phone_number=user.phone_number, is_used=False).delete
    )()

    code = str(random.randint(100000, 999999))

    await sync_to_async(OTPCode.objects.create)(
        phone_number=user.phone_number,
        chat_id=chat_id,
        username=user.name or '',
        code=code
    )

    sent_message = await update.message.reply_text(
        f"🔐 Sizning login kodingiz:\n\n"
        f"`{code}`\n\n"
        f"Kod 60 soniyada eskiradi.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Yangilash", callback_data=f"renew_{user.phone_number}")
        ]])
    )

    context.job_queue.run_once(
        expire_code_message,
        60,
        data={
            'chat_id': chat_id,
            'message_id': sent_message.message_id,
            'phone': user.phone_number
        }
    )


async def renew_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        remaining = max(0, int(60 - (timezone.now() - existing_otp.created_at).total_seconds()))

        await query.answer(
            text=f"Eski kodingiz hali ham amal qiladi, iltimos uni ishlating yoki {remaining} soniya kuting.",
            show_alert=True
        )
        return

    # answer — har doim chaqirilishi kerak
    await query.answer()

    await sync_to_async(
        OTPCode.objects.filter(phone_number=phone, is_used=False).delete
    )()

    code = str(random.randint(100000, 999999))

    await sync_to_async(OTPCode.objects.create)(
        phone_number=phone,
        chat_id=chat_id,
        username='',
        code=code
    )

    sent_message = await query.edit_message_text(
        f"🔐 Sizning yangi login kodingiz:\n\n"
        f"`{code}`\n\n"
        f"Kod 60 soniyada eskiradi.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Yangilash", callback_data=f"renew_{phone}")
        ]])
    )

    context.job_queue.run_once(
        expire_code_message,
        60,
        data={
            'chat_id': chat_id,
            'message_id': sent_message.message_id,
            'phone': phone
        }
    )


async def expire_code_message(context: ContextTypes.DEFAULT_TYPE):
    """60 soniyadan keyin xabarni yangilash"""
    data = context.job.data
    try:
        await context.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text="🔒 Kod muddati tugadi. <b>yangilash</b> tugmasini bosib, yangi kod oling.\n\n",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Yangilash", callback_data=f"renew_{data['phone']}")
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
