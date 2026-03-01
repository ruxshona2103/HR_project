from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    AccountUserProfileSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class EmailTokenRefreshView(TokenRefreshView):
    @extend_schema(tags=["Email Auth"], summary="Email Auth — Token yangilash")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(tags=["Email Auth"],
        summary="Ro'yxatdan o'tish",
        description="Email + parol bilan yangi account yaratish. Telefon raqam ixtiyoriy.",
               )
class RegisterView(generics.CreateAPIView):
    """Yangi foydalanuvchi ro'yxatdan o'tkazish"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Email Auth"],
        summary="Ro'yxatdan o'tish",
        description="Email + parol bilan yangi account yaratish. Telefon raqam ixtiyoriy.",
        responses={
            201: OpenApiResponse(description="Muvaffaqiyatli ro'yxatdan o'tdi + tokenlar qaytadi"),
            400: OpenApiResponse(description="Validatsiya xatosi"),
        },
        examples=[
            OpenApiExample(
                "Misol so'rov",
                value={
                    "email": "ali@example.com",
                    "first_name": "Ali",
                    "last_name": "Valiyev",
                    "phone_number": "+998901234567",
                    "password": "StrongPass123!",
                    "password_confirm": "StrongPass123!",
                },
                request_only=True,
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number,
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Email + Parol bilan kirish"""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Email Auth"],
        summary="Kirish (Login)",
        description="Email va parol bilan kirish. Access (1 soat) va Refresh (7 kun) token qaytaradi.",
        request=LoginSerializer,
        examples=[
            OpenApiExample(
                "Misol so'rov",
                value={"email": "ali@example.com", "password": "StrongPass123!"},
                request_only=True,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)



class LogoutView(APIView):
    """Chiqish - refresh tokenni blacklistga qo'shish"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Email Auth"],
        summary="Chiqish (Logout)",
        description="Refresh tokenni bekor qiladi. Keyinchalik bu token ishlamaydi.",
        examples=[
            OpenApiExample(
                "Misol so'rov",
                value={"refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"success": False, "message": "refresh token kiritilmadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"success": True, "message": "Muvaffaqiyatli chiqdingiz."},
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                {"success": False, "message": "Token noto'g'ri yoki allaqachon bekor qilingan."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Profil ko'rish (GET) va tahrirlash (PATCH)"""
    serializer_class = AccountUserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    @extend_schema(tags=["Profil"], summary="Profilni ko'rish")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Profil"], summary="Profilni tahrirlash")
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class ChangePasswordView(APIView):
    """Parolni o'zgartirish"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Profil"],
        summary="Parolni o'zgartirish",
        request=ChangePasswordSerializer,
        examples=[
            OpenApiExample(
                "Misol so'rov",
                value={
                    "old_password": "OldPass123!",
                    "new_password": "NewPass456!",
                    "new_password_confirm": "NewPass456!",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"success": True, "message": "Parol muvaffaqiyatli o'zgartirildi."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Joriy foydalanuvchi ma'lumotlari (token bo'yicha)"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Profil"],
        summary="Men kimman?",
        description="Token orqali joriy foydalanuvchi ma'lumotlarini olish.",
        responses=AccountUserProfileSerializer,
    )
    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.get_full_name(),
            "phone_number": user.phone_number,
            "is_staff": user.is_staff,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
        })
