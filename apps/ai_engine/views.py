import json
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import InterviewResult
from .services.interview_service import ResumeService
from apps.vacancies.models import Vacancy


@extend_schema(tags=["AI Engine"])
class ResumeCheckAPIView(APIView):
    """
    Nomzod rezyumesini vakansiyaga mosligini tekshirish uchun API.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        vacancy_id = request.data.get('vacancy_id')
        resume_text = request.data.get('resume_text')

        if not vacancy_id or not resume_text:
            return Response(
                {"error": "vacancy_id va resume_text yuborilishi shart"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = ResumeService()
            analysis_result_str = service.analyze_resume(resume_text, vacancy_id)

            try:
                analysis_result = json.loads(analysis_result_str)
            except json.JSONDecodeError:
                analysis_result = {"raw_response": analysis_result_str}

            return Response(analysis_result, status=status.HTTP_200_OK)
        except Vacancy.DoesNotExist:
            return Response({"error": "Vakansiya topilmadi"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(
                {"error": "Rezyumeni tahlil qilishda ichki xatolik yuz berdi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=["AI Engine"])
class InterviewStartAPIView(APIView):
    """
    Intervyuni boshlash uchun (WebSocket ulanishidan oldin ma'lumot olish).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, vacancy_id):
        try:
            vacancy = Vacancy.objects.get(id=vacancy_id)
            return Response({
                "vacancy_title": vacancy.title,
                "status": "ready_for_interview",
                "ws_url": f"ws://{request.get_host()}/ws/interview/{vacancy_id}/?token=<JWT_ACCESS_TOKEN>",
            })
        except Vacancy.DoesNotExist:
            return Response({"error": "Vakansiya topilmadi"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=["AI Engine"])
class InterviewStatusAPIView(APIView):
    """
    Nomzod ma'lum bir vakansiya bo'yicha AI-intervyudan o'tganmi yoki
    yo'qligini tekshiradi. Faqat autentifikatsiyadan o'tgan foydalanuvchi
    o'zining natijasini ko'radi (JWT orqali — DRF standart autentifikatsiyasi).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, vacancy_id):
        result = (
            InterviewResult.objects
            .filter(user=request.user, vacancy_name=str(vacancy_id))
            .order_by('-created_at')
            .first()
        )

        if result:
            return Response({
                "status": "completed",
                "result_id": result.id,
                "score": result.score,
            })
        return Response({"status": "not_started"})


@extend_schema(tags=["AI Engine"])
class InterviewFeedbackAPIView(APIView):
    """
    AI-intervyu natijasi va xulosasini ko'rsatadi.
    Faqat natijaning egasi (shu intervyuni topshirgan foydalanuvchi)
    uni ko'rishi mumkin — boshqa foydalanuvchining natijasi 403 bilan yopiladi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, result_id):
        try:
            result = InterviewResult.objects.get(id=result_id)
        except InterviewResult.DoesNotExist:
            return Response({"error": "Natija topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if result.user_id != request.user.id:
            return Response(
                {"error": "Sizda bu natijani ko'rish huquqi yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({
            'feedback': result.feedback,
            'score': result.score,
            'chat_history': result.chat_log,
        })