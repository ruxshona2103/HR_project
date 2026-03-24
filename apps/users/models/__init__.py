# from .user import User, UserManager
# from .otp import OTPCode, EmailOTPCode, PendingRegistration
# from .attempt import OTPAttempt
#
# __all__ = ['User', 'UserManager', 'OTPCode', 'EmailOTPCode', 'OTPAttempt', 'PendingRegistration']
from .user import User
from .otp import OTPCode, EmailOTPCode, PendingRegistration
from .attempt import OTPAttempt
from .email_verification import EmailVerificationCode  # ← YANGI



__all__ = ['User', 'UserManager', 'OTPCode', 'EmailOTPCode', 'OTPAttempt', 'PendingRegistration']