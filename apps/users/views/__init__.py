from .auth import (
    CandidateRegisterView,
    OrganizationRegisterView,
    LoginView,
    LogoutView
)
from .otp import VerifyOTPView
from .profile import MeView, ChangePasswordView, DeleteAccountView
from .other import BotLinkView

__all__ = [
    'CandidateRegisterView',
    'OrganizationRegisterView',
    'LoginView',
    'LogoutView',
    'VerifyOTPView',
    'MeView',
    'ChangePasswordView',
    'BotLinkView',
    'DeleteAccountView',
]