import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.ai_engine.services.interview_service import AIInterviewEngine
import logging

logger = logging.getLogger(__name__)

class InterviewConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.vacancy_id = self.scope['url_route']['kwargs'].get('vacancy_id')

        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)  # Unauthorized access
            return

        self.room_group_name = f"interview_{self.vacancy_id}_{self.user.id}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        try:
            init_engine = database_sync_to_async(
                lambda: AIInterviewEngine(vacancy_id=self.vacancy_id, user=self.user)
            )
            self.interview_engine = await init_engine()

            initial_greeting = "Assalomu alaykum! Altron tizimiga xush kelibsiz. Suhbatni boshlashga tayyormisiz?"
            await self.send(text_data=json.dumps({
                'type': 'ai_message',
                'message': initial_greeting
            }))
        except Exception as e:
            logger.error(f"WebSocket xatoligi: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error_message',
                'message': "Kechirasiz, tizimda ichki xatolik yuz berdi."
            }))
            await self.close(code=4002)


    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            user_message = data.get('message')

            if not user_message:
                return

            # 4. Gemini API chaqiruvini database_sync_to_async yordamida to'g'ri va xavfsiz bajarish
            get_ai_response = database_sync_to_async(
                self.interview_engine.get_next_response
            )
            ai_response = await get_ai_response(user_message)

            await self.send(text_data=json.dumps({
                'type': 'ai_message',
                'message': ai_response
            }))

            if "SUHBAT YAKUNLANDI" in ai_response:
                await self.send(text_data=json.dumps({
                    'type': 'system_message',
                    'message': 'Suhbat muvaffaqiyatli yakunlandi. Natijalar HR panelida paydo bo\'ladi.'
                }))
                await self.close(code=1000)


        except Exception as e:

            logger.error(f"WebSocket xatoligi: {str(e)}")

            await self.send(text_data=json.dumps({

                'type': 'error_message',

                'message': "Kechirasiz, tizimda ichki xatolik yuz berdi."

            }))
            await self.close(code=4002)
