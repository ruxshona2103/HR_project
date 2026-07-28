from rest_framework.throttling import AnonRateThrottle


class OTPRequestThrottle(AnonRateThrottle):
    """OTP so'rash uchun throttle — 5 ta/daqiqa"""
    scope = "otp_request"