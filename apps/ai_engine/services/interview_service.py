import google.generativeai as genai
from django.conf import settings
from apps.vacancies.models import Vacancy
from ..prompts.templates import INTERVIEWER_PROMPT,EVALUATION_PROMPT



class AIInterviewEngine:
    def __init__(self, vacancy_id):
        # Gemini sozlamalari
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        # Siz tashlagan Vacancy modelidan ma'lumotni olamiz
        vacancy = Vacancy.objects.get(id=vacancy_id)

        # AI uchun ko'rsatma (Prompt)
        self.system_instruction =INTERVIEWER_PROMPT


        # Suhbatni xotira (history) bilan boshlaymiz
        self.chat = self.model.start_chat(history=[])
        self.chat.send_message(self.system_instruction)

    def get_next_response(self, user_text):
        """Nomzodning matnli yoki ovozli (matnga o'girilgan) javobini qabul qiladi"""
        try:
            response = self.chat.send_message(user_text)
            return response.text
        except Exception as e:
            return "Kechirasiz, tizimda xatolik yuz berdi. Qaytadan urinib ko'ring."

class AIEvaluator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def evaluate_interview(self, vacancy_name, chat_history):
        # Suhbat tarixini matn ko'rinishiga keltiramiz
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])

        prompt = EVALUATION_PROMPT.format(
            vacancy_name=vacancy_name,
            chat_history=history_text
        )

        try:
            # Baholash natijasini generatsiya qilish
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return "Baholashda xatolik yuz berdi."


