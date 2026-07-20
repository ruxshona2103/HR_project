from django.http import JsonResponse
from .models import InterviewResult
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.resume_service import ResumeService
from apps.vacancies.models import Vacancy


def get_interview_status(request, vacancy_id):
    """Nomzod suhbatdan o'tganmi yoki yo'qligini tekshirish"""
    result = InterviewResult.objects.filter(user=request.user, vacancy_name=vacancy_id).first()
    if result:
        return JsonResponse({'status': 'completed', 'score': result.score})
    return JsonResponse({'status': 'not_started'})

def get_ai_feedback(request, result_id):
    """HR yoki Nomzod uchun AI xulosasini ko'rsatish"""
    result = InterviewResult.objects.get(id=result_id)
    return JsonResponse({
        'feedback': result.feedback,
        'score': result.score,
        'chat_history': result.chat_log
    })


def check_resume_view(request):
    if request.method == "POST":
        resume_file = request.FILES.get('resume')
        vacancy_desc = request.POST.get('vacancy_description')

        # Rezyume tahlili xizmatini chaqiramiz
        service = ResumeService()
        analysis = service.analyze(resume_file, vacancy_desc)

        return JsonResponse({
            'match_score': analysis['score'],
            'suggestions': analysis['tips']
        })

class ResumeCheckAPIView(APIView):
    """
    Nomzod rezyumesini vakansiyaga mosligini tekshirish uchun API
    """
    def post(self, request):
        vacancy_id = request.data.get('vacancy_id')
        resume_text = request.data.get('resume_text') # Front-end PDF dan matnni olib beradi

        if not vacancy_id or not resume_text:
            return Response(
                {"error": "vacancy_id va resume_text yuborilishi shart"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = ResumeService()
            # AI tahlilini olamiz
            analysis_result = service.analyze_resume(resume_text, vacancy_id)
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
                "ws_url": f"ws://your-domain/ws/interview/{vacancy_id}/"
            })
        except Vacancy.DoesNotExist:
            return Response({"error": "Vakansiya topilmadi"}, status=status.HTTP_404_NOT_FOUND)