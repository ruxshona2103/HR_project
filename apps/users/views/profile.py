from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from apps.users.serializers import AccountUserProfileSerializer, ChangePasswordSerializer


@extend_schema(
    tags=["Profile"],
    summary="Profil",
    description="GET — profil ko'rish, PATCH — profil tahrirlash",
    responses={200: AccountUserProfileSerializer}
)
class MeView(APIView):
    """Profil"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = AccountUserProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=AccountUserProfileSerializer,
        examples=[
            OpenApiExample(
                "Ismni o'zgartirish",
                value={"first_name": "Yangi Ism", "last_name": "Yangi Familya"},
                request_only=True
            )
        ]
    )
    def patch(self, request):
        serializer = AccountUserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Profile"],
    summary="Parolni o'zgartirish",
    request=ChangePasswordSerializer,
    examples=[
        OpenApiExample(
            "Parolni o'zgartirish",
            value={
                "old_password": "OldPass123!",
                "new_password": "NewPass456!",
                "new_password_confirm": "NewPass456!"
            },
            request_only=True
        )
    ],
    responses={200: OpenApiResponse(description="Parol o'zgartirildi")}
)
class ChangePasswordView(APIView):
    """Parolni o'zgartirish"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Parol muvaffaqiyatli o'zgartirildi"},
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Profile"],
    summary="Accountni o'chirish",
    description="Account butunlay o'chiriladi. Bu operatsiyani qaytarib bo'lmaydi!",
    responses={
        204: OpenApiResponse(description="Account o'chirildi"),
    }
)
class DeleteAccountView(APIView):
    """Account butunlay o'chirish"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()

        return Response(
            {"message": "Account butunlay o'chirildi"},
            status=status.HTTP_204_NO_CONTENT
        )
