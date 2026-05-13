import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .services.interview_service import AIInterviewEngine


class InterviewConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # URL'dan vakansiya ID'sini olamiz (masalan: ws/interview/5/)
        self.vacancy_id = self.scope['url_route']['kwargs']['vacancy_id']

        # AI motorini ishga tushiramiz
        # Eslatma: AIInterviewEngine sinxron bo'lsa, bu yerda async muammosi bo'lmasligi uchun
        # mantiqni biroz soddalashtiramiz yoki sync_to_async dan foydalanamiz
        self.interview_engine = AIInterviewEngine(self.vacancy_id)

        await self.accept()

        # Birinchi bo'lib AI nomzod bilan salomlashadi
        initial_greeting = "Assalomu alaykum! Altron tizimiga xush kelibsiz. Suhbatni boshlashga tayyormisiz?"
        await self.send(text_data=json.dumps({
            'type': 'ai_message',
            'message': initial_greeting
        }))

    async def disconnect(self, close_code):
        # Aloqa uzilganda xotirani tozalash yoki natijani saqlash mumkin
        pass

    async def receive(self, text_data):
        """Nomzoddan kelgan xabarni (matn yoki STT natijasi) qabul qilish"""
        data = json.loads(text_data)
        user_message = data.get('message')

        if user_message:
            # Gemini'dan javob olish
            ai_response = self.interview_engine.get_next_response(user_message)

            # Javobni nomzodga yuborish
            await self.send(text_data=json.dumps({
                'type': 'ai_message',
                'message': ai_response
            }))

            # Agar intervyu tugagan bo'lsa, ulanishni yopish haqida signal berish
            if "SUHBAT YAKUNLANDI" in ai_response:
                await self.send(text_data=json.dumps({
                    'type': 'system_message',
                    'message': 'Suhbat muvaffaqiyatli yakunlandi. Natijalar HR panelida paydo bo\'ladi.'
                }))