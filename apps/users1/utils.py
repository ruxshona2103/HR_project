import logging
import resend
from django.conf import settings
from rest_framework import serializers

logger = logging.getLogger(__name__)


def send_verification_email(email: str, code: str):
    """
    Tasdiqlash kodini Resend orqali yuboruvchi yordamchi funksiya.
    DRY qoidasiga amal qilish uchun shablon shu yerga jamlandi.
    """
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color:#2563eb; text-align:center;">
            HR Project
        </h2>
        <p>Assalomu alaykum!</p>
        <p>Email manzilingizni tasdiqlash uchun quyidagi koddan foydalaning:</p>
        <div style="text-align:center; margin:30px 0;">
            <span style="
                display:inline-block;
                padding:15px 35px;
                font-size:42px;
                font-weight:bold;
                letter-spacing:6px;
                background:#f3f4f6;
                border-radius:10px;
                color:#111827;
            ">
                {code}
            </span>
        </div>
        <p><b>Kod 5 daqiqa amal qiladi.</b></p>
        <p>Agar bu so'rovni siz yubormagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring.</p>
        <br>
        <p>
            Hurmat bilan,<br>
            <b>HR Project jamoasi</b>
        </p>
    </div>
    """

    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [email],
            "subject": "HR Project — Email Tasdiqlash",
            "html": html_content,
        })
    except Exception as e:
        logger.error(f"Email yuborishda xato ({email}): {e}")
        raise serializers.ValidationError(
            {"email": "Email yuborishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."}
        )