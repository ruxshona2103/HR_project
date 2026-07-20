from rest_framework.throttling import AnonRateThrottle


class OTPRequestThrottle(AnonRateThrottle):
    """OTP so'rash uchun throttle — 1 ta/daqiqa"""
    rate = "1/min"
