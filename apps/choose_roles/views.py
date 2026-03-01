from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import RoleSelectionSerializer
from .services import SetUserRoleAction


class ChooseRoleView(APIView):
    """
    Foydalanuvchiga rol tanlash imkonini beruvchi API Endpoint.
    Faqat avtorizatsiyadan o'tgan (login qilgan) foydalanuvchilar kira oladi.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Ma'lumotni validatsiya qilish
        serializer = RoleSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data['role']

        # 2. Biznes mantiqni (Action) ishga tushirish
        action = SetUserRoleAction(user=request.user, role=role)
        action.execute()

        # 3. Natijani qaytarish
        return Response(
            {"message": f"Tabriklaymiz! Siz {role} sifatida ro'yxatdan o'tdingiz."},
            status=status.HTTP_200_OK
        )