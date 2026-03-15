from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_id = username or kwargs.get('email') or kwargs.get('username')

        if login_id is None or password is None:
            return None

        try:
        # Foydalanuvchini email, telefon yoki vaqtincha format orqali qidiramiz
            user = User.objects.filter(
                Q(email__iexact=login_id) |
                Q(phone_number__iexact=login_id) |
                Q(email__iexact=f"phone_{login_id}@temporary.local")
            ).distinct().first()

            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        except Exception:
            return None
        return None
