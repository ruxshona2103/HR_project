from .phone_auth import (
    PhoneCandidateRegisterView,
    PhoneOrganizationRegisterView,
    PhoneLoginRequestView,
    OTPVerifyView,
)
from .email_auth import (
    EmailLoginView,
    EmailCandidateRegisterView,
    EmailOrganizationRegisterView,
    VerifyEmailView,
    ResendEmailCodeView,
)
from .profile import (
    MeView,
    ChangePasswordView,
    LogoutView,
    DeleteAccountView,
    BotLinkView,
)
from .telegram_connect_views import (
    TelegramConnectView,
    TelegramDisconnectView,
    TelegramStatusView,
    SendVacancyNotificationView,)
__all__ = [
    'PhoneCandidateRegisterView',
    'PhoneOrganizationRegisterView',
    'PhoneLoginRequestView',
    'OTPVerifyView',

    'EmailLoginView',
    'EmailCandidateRegisterView',
    'EmailOrganizationRegisterView',
    'VerifyEmailView',
    'ResendEmailCodeView',

    'MeView',
    'ChangePasswordView',
    'LogoutView',
    'DeleteAccountView',
    'BotLinkView',

    'TelegramConnectView',
    'TelegramDisconnectView',
    'TelegramStatusView',
    'SendVacancyNotificationView',
]
