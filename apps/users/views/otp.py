from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import OTPCode, OTPAttempt, User, PendingRegistration
from apps.users.serializers import VerifyOTPSerializer
from apps.users.throttling import OTPRequestThrottle


@extend_schema(
    tags=["Auth"],
    summary="OTP kodni tasdiqlash",
    description="Telefon orqali ro'yxatdan o'tganda OTP kodni tasdiqlash. Kod to'g'ri bo'lsa User yaratiladi va JWT tokenlar qaytadi.",
    request=VerifyOTPSerializer,
    examples=[
        OpenApiExample(
            "OTP tasdiqlash",
            value={"phone_number": "+998901234567", "code": "123456"},
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(description="Login — JWT tokenlar"),
        201: OpenApiResponse(description="Register — JWT tokenlar"),
    }
)
class VerifyOTPView(APIView):
    throttle_classes = [OTPRequestThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']

        attempt, _ = OTPAttempt.objects.get_or_create(phone_number=phone)

        if attempt.is_blocked():
            return Response(
                {'error': "Telefon raqam bloklangan. 10 daqiqadan keyin urinib ko'ring"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        try:
            otp = OTPCode.objects.get(phone_number=phone, code=code, is_used=False)
        except OTPCode.DoesNotExist:
            attempt.add_attempt()
            remaining = 5 - attempt.attempts
            return Response(
                {"error": f"Kod noto'g'ri. {remaining} ta urinish qoldi"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.is_expired():
            attempt.add_attempt()
            return Response(
                {"error": "Kod muddati tugagan"},
                status=status.HTTP_400_BAD_REQUEST
            )

        attempt.reset()
        otp.is_used = True
        otp.save()

        existing_user = User.objects.filter(phone_number=phone).first()

        if existing_user:
            refresh = RefreshToken.for_user(existing_user)
            return Response({
                'message': "Muvaffaqiyatli kirildi",
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'user': {
                    'id': existing_user.id,
                    'phone_number': existing_user.phone_number,
                    'first_name': existing_user.first_name,
                    'user_type': existing_user.user_type,
                }
            }, status=status.HTTP_200_OK)

        try:
            pending = PendingRegistration.objects.get(phone_number=phone)
        except PendingRegistration.DoesNotExist:
            return Response(
                {"error": "Ro'yxat ma'lumotlari topilmadi. Qaytadan ro'yxatdan o'ting"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if pending.is_expired():
            pending.delete()
            return Response(
                {"error": "Ro'yxat muddati tugagan. Qaytadan urinib ko'ring"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create(
            phone_number=phone,
            email=f"phone_{phone}@temporary.local",
            password=pending.password_hash,
            user_type=pending.user_type,
            first_name=pending.first_name,
            last_name=pending.last_name,
            middle_name=pending.middle_name,
            organization_name=pending.organization_name,
            position=pending.position,
            chat_id=otp.chat_id,
        )

        pending.delete()

        refresh = RefreshToken.for_user(user)

        return Response({
            'message': "Muvaffaqiyatli ro'yxatdan o'tdingiz",
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'first_name': user.first_name,
                'user_type': user.user_type,
            }
        }, status=status.HTTP_201_CREATED)