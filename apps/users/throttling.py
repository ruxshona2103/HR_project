from rest_framework.throttling import AnonRateThrottle
from django.conf import settings


class OTPRequestThrottle(AnonRateThrottle):
    scope = 'otp_request'

    def allow_request(self, request, view):
        """Test qilganda o'chirilgan bo'ladi"""
        if getattr(settings, 'TESTING', False):
            return True
        return super().allow_request(request, view)
