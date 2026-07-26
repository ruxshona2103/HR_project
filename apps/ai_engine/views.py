from django.http import JsonResponse
from .models import InterviewResult
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.interview_service import ResumeService
from apps.vacancies.models import Vacancy
import json


def get_interview_status(request, vacancy_id):
    """Nomzod suhbatdan o'tganmi yoki yo'qligini tekshirish"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    result = InterviewResult.objects.filter(user=request.user, vacancy_name=str(vacancy_id)).first()
    if result:
        return JsonResponse({'status': 'completed', 'score': result.score})
    return JsonResponse({'status': 'not_started'})


def get_ai_feedback(request, result_id):
    """HR yoki Nomzod uchun AI xulosasini ko'rsatish"""
    try:
        result = InterviewResult.objects.get(id=result_id)
        return JsonResponse({
            'feedback': result.feedback,
            'score': result.score,
            'chat_history': result.chat_log
        })
    except InterviewResult.DoesNotExist:
        return JsonResponse({'error': 'Natija topilmadi'}, status=404)


class ResumeCheckAPIView(APIView):
    """
    Nomzod rezyumesini vakansiyaga mosligini tekshirish uchun API
    """

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
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InterviewStartAPIView(APIView):
    """
    Intervyuni boshlash uchun (Websocket ulanishidan oldin ma'lumot olish)
    """
    def get(self, request, vacancy_id):
        try:
            vacancy = Vacancy.objects.get(id=vacancy_id)
            return Response({
                "vacancy_title": vacancy.title,
                "status": "ready_for_interview",
                "ws_url": f"ws://{request.get_host()}/ws/interview/{vacancy_id}/"
            })
        except Vacancy.DoesNotExist:
            return Response({"error": "Vakansiya topilmadi"}, status=status.HTTP_404_NOT_FOUND)