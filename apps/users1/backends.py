from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Email + parol bilan kirish uchun backend.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 'username' o'rniga 'email' ham qabul qilinadi
        email = username or kwargs.get('email')

        if not email or not password:
            return None

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
