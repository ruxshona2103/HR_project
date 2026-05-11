import google.generativeai as genai
from django.conf import settings
from apps.vacancies.models import Vacancy
from ..prompts.templates import RESUME_CHECK_PROMPT


class ResumeService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_resume(self, resume_text, vacancy_id):
        """Rezyume matnini va vakansiya ID-sini qabul qilib, tahlil qaytaradi"""
        vacancy = Vacancy.objects.get(id=vacancy_id)

        prompt = RESUME_CHECK_PROMPT

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return "{\"error\": \"AI tahlil qila olmadi\"}"