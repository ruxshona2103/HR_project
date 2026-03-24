from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.contrib.auth.hashers import make_password
from apps.users.serializers import (
    CandidateRegisterSerializer,
    OrganizationRegisterSerializer,
    LoginSerializer,
    LogoutRequestSerializer
)
from apps.users.models import PendingRegistration


@extend_schema(
    tags=["Auth"],
    summary="Nomzod ro'yxatdan o'tish",
    description="Nomzod (ish izlovchi) ro'yxatdan o'tish. Email yoki telefon orqali.",
    request=CandidateRegisterSerializer,
    examples=[
        OpenApiExample(
            "Email orqali",
            value={
                "auth_method": "email",
                "email": "candidate@example.com",
                "first_name": "Ali",
                "last_name": "Valiyev",
                "middle_name": "Akbarovich",
                "phone_number": "+998901234567",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!"
            },
            request_only=True
        ),
        OpenApiExample(
            "Telefon orqali",
            value={
                "auth_method": "phone",
                "phone_number": "+998901234567",
                "first_name": "Ali",
                "last_name": "Valiyev",
                "middle_name": "Akbarovich",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!"
            },
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(description="Telefon orqali — OTP yuborildi"),
        201: OpenApiResponse(description="Email orqali — User yaratildi"),
    }
)
class CandidateRegisterView(generics.CreateAPIView):
    """Nomzod ro'yxatdan o'tish"""
    serializer_class = CandidateRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_method = serializer.validated_data.get('auth_method')

        if auth_method == 'phone':
            phone = serializer.validated_data['phone_number']

            PendingRegistration.objects.update_or_create(
                phone_number=phone,
                defaults={
                    'user_type': 'candidate',
                    'password_hash': make_password(serializer.validated_data['password']),
                    'first_name': serializer.validated_data.get('first_name', ''),
                    'last_name': serializer.validated_data.get('last_name', ''),
                    'middle_name': serializer.validated_data.get('middle_name', ''),
                }
            )

            return Response({
                "message": "Telegram botga OTP kod yuborildi. Botdan kodni oling va tasdiqlang.",
                "phone_number": phone,
                "next_step": "/api/users/auth/verify-otp/"
            }, status=status.HTTP_200_OK)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_type": user.user_type,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="Tashkilot ro'yxatdan o'tish",
    description="Tashkilot (ish beruvchi) ro'yxatdan o'tish. Email yoki telefon orqali.",
    request=OrganizationRegisterSerializer,
    examples=[
        OpenApiExample(
            "Email orqali",
            value={
                "auth_method": "email",
                "email": "company@example.com",
                "organization_name": "ABC Company",
                "position": "HR Manager",
                "first_name": "Vali",
                "last_name": "Valiyev",
                "middle_name": "Valievich",
                "phone_number": "+998901234567",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!"
            },
            request_only=True
        ),
        OpenApiExample(
            "Telefon orqali",
            value={
                "auth_method": "phone",
                "phone_number": "+998901234567",
                "organization_name": "ABC Company",
                "position": "HR Manager",
                "first_name": "Vali",
                "last_name": "Valiyev",
                "middle_name": "Valievich",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!"
            },
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(description="Telefon orqali — OTP yuborildi"),
        201: OpenApiResponse(description="Email orqali — User yaratildi"),
    }
)
class OrganizationRegisterView(generics.CreateAPIView):
    """Tashkilot ro'yxatdan o'tish"""
    serializer_class = OrganizationRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_method = serializer.validated_data.get('auth_method')

        if auth_method == 'phone':
            phone = serializer.validated_data['phone_number']

            PendingRegistration.objects.update_or_create(
                phone_number=phone,
                defaults={
                    'user_type': 'organization',
                    'password_hash': make_password(serializer.validated_data['password']),
                    'first_name': serializer.validated_data.get('first_name', ''),
                    'last_name': serializer.validated_data.get('last_name', ''),
                    'middle_name': serializer.validated_data.get('middle_name', ''),
                    'organization_name': serializer.validated_data.get('organization_name'),
                    'position': serializer.validated_data.get('position'),
                }
            )

            return Response({
                "message": "Telegram botga OTP kod yuborildi. Botdan kodni oling va tasdiqlang.",
                "phone_number": phone,
                "next_step": "/api/users/auth/verify-otp/"
            }, status=status.HTTP_200_OK)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz",
            "user": {
                "id": user.id,
                "email": user.email,
                "organization_name": user.organization_name,
                "position": user.position,
                "user_type": user.user_type,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="Login",
    description="Email yoki telefon + parol bilan kirish. JWT tokenlar qaytaradi.",
    request=LoginSerializer,
    examples=[
        OpenApiExample(
            "Email bilan",
            value={"email": "user@example.com", "password": "StrongPass123!"},
            request_only=True
        ),
        OpenApiExample(
            "Telefon bilan",
            value={"phone_number": "+998901234567", "password": "StrongPass123!"},
            request_only=True
        )
    ],
    responses={200: OpenApiResponse(description="JWT tokenlar qaytadi")}
)
class LoginView(APIView):
    """Login"""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Logout"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Logout",
        description="Refresh tokenni blacklist qilish. Token bekor qilinadi.",
        request=LogoutRequestSerializer,
        examples=[
            OpenApiExample(
                "Logout namuna",
                value={"refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"},
                request_only=True
            )
        ],
        responses={
            200: OpenApiResponse(description="Muvaffaqiyatli chiqildi"),
            400: OpenApiResponse(description="Xato ma'lumot yuborildi")
        }
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "refresh token kiritilmadi"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Muvaffaqiyatli chiqildi"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Yaroqsiz yoki eskirgan refresh token"}, status=status.HTTP_400_BAD_REQUEST)