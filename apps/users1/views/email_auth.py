from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from apps.users1.serializers import (
    EmailLoginSerializer,
    EmailCandidateRegisterSerializer,
    EmailOrganizationRegisterSerializer,
    VerifyEmailSerializer,
    ResendEmailCodeSerializer,
)


@extend_schema(tags=["Email Auth"])
class EmailLoginView(APIView):
    """Email + Parol bilan kirish"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Email va parol bilan kirish",
        request=EmailLoginSerializer,
        responses={
            200: OpenApiResponse(description="JWT tokenlar qaytadi"),
            400: OpenApiResponse(description="Email yoki parol noto'g'ri"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={"email": "user@gmail.com", "password": "StrongPass123!"},
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Email Auth"])
class EmailCandidateRegisterView(APIView):
    """Email orqali nomzod ro'yxatdan o'tish — 1-qadam"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Email orqali nomzod ro'yxatdan o'tish",
        request=EmailCandidateRegisterSerializer,
        responses={
            200: OpenApiResponse(description="Tasdiqlash kodi emailga yuborildi"),
            400: OpenApiResponse(description="Validatsiya xatosi"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={
                    "email": "candidate@gmail.com",
                    "first_name": "Ali",
                    "last_name": "Valiyev",
                    "middle_name": "Akbarovich",
                    "password": "StrongPass123!",
                    "password_confirm": "StrongPass123!",
                },
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = EmailCandidateRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Tasdiqlash kodi emailingizga yuborildi.",
                "email": serializer.validated_data['email'],
                "next_step": "/api/users/auth/email/verify/",
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Email Auth"])
class EmailOrganizationRegisterView(APIView):
    """Email orqali tashkilot ro'yxatdan o'tish — 1-qadam"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Email orqali tashkilot ro'yxatdan o'tish",
        request=EmailOrganizationRegisterSerializer,
        responses={
            200: OpenApiResponse(description="Tasdiqlash kodi emailga yuborildi"),
            400: OpenApiResponse(description="Validatsiya xatosi"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={
                    "email": "hr@company.com",
                    "first_name": "Vali",
                    "last_name": "Valiyev",
                    "organization_name": "ABC Company",
                    "position": "HR Manager",
                    "password": "StrongPass123!",
                    "password_confirm": "StrongPass123!",
                },
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = EmailOrganizationRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Tasdiqlash kodi emailingizga yuborildi.",
                "email": serializer.validated_data['email'],
                "next_step": "/api/users/auth/email/verify/",
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Email Auth"])
class VerifyEmailView(APIView):
    """Email kodni tasdiqlash va User yaratish — 2-qadam"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Email kodni tasdiqlash",
        request=VerifyEmailSerializer,
        responses={
            201: OpenApiResponse(description="Muvaffaqiyatli ro'yxatdan o'tdingiz, JWT token"),
            400: OpenApiResponse(description="Kod noto'g'ri yoki eskirgan"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={"email": "user@gmail.com", "code": "123456"},
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz!",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "user_type": user.user_type,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Email Auth"])
class ResendEmailCodeView(APIView):
    """Email tasdiqlash kodini qayta yuborish"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Email kodini qayta yuborish",
        request=ResendEmailCodeSerializer,
        responses={
            200: OpenApiResponse(description="Yangi kod yuborildi"),
            400: OpenApiResponse(description="Email topilmadi"),
        },
        examples=[
            OpenApiExample(
                "Misol",
                value={"email": "user@gmail.com"},
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = ResendEmailCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Yangi tasdiqlash kodi emailingizga yuborildi.",
                "email": serializer.validated_data['email'],
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
