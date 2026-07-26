from google import genai
from django.conf import settings
from apps.vacancies.models import Vacancy
from ..prompts.templates import (
    get_interviewer_prompt,
    get_evaluation_prompt,
    get_resume_check_prompt
)
from google.genai import types
import logging

logger = logging.getLogger(__name__)


class BaseAIService:
    """DRY tamoyili uchun umumiy bazaviy AI xizmati klassi"""
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_KEY,
            http_options=types.HttpOptions(api_version='v1')
        )
        self.model_name = "gemini-2.0-flash"

class AIInterviewEngine(BaseAIService):
    def __init__(self, vacancy_id, user=None):
        super().__init__()
        vacancy = Vacancy.objects.get(id=vacancy_id)
        self.system_instruction = get_interviewer_prompt(vacancy)

        self.chat = self.client.chats.create(
            model=self.model_name,
            config={'system_instruction': self.system_instruction}
        )

    def get_next_response(self, user_text):
        try:
            response = self.chat.send_message(user_text)
            return response.text
        except Exception as e:
            logger.error(f"AI Interview xatosi: {str(e)}")
            return "Kechirasiz, tizimda xatolik yuz berdi. Qaytadan urinib ko'ring."


class AIEvaluator(BaseAIService):
    def evaluate_interview(self, vacancy_id, chat_history):
        vacancy = Vacancy.objects.get(id=vacancy_id)
        history_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in chat_history])
        prompt = get_evaluation_prompt(vacancy, history_text)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"AI Evaluator xatosi: {str(e)}")
            return "Baholashda xatolik yuz berdi."


class ResumeService(BaseAIService):
    def analyze_resume(self, resume_text, vacancy_id):
        vacancy = Vacancy.objects.get(id=vacancy_id)
        prompt = get_resume_check_prompt(vacancy, resume_text)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Resume Service xatosi: {str(e)}")
            return '{"error": "AI tahlil qila olmadi"}'