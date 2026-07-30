import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from apps.ai_engine.services.interview_service import AIInterviewEngine, AIEvaluator
from apps.ai_engine.models import InterviewResult
from apps.vacancies.models import Vacancy

logger = logging.getLogger(__name__)

INTERVIEW_END_MARKER = "SUHBAT YAKUNLANDI"

# Xavfsizlik chegarasi: agar AI o'z vaqtida "SUHBAT YAKUNLANDI" demasa ham,
# intervyu abadiy davom etib, token/xarajat portlab ketmasligi uchun.
MAX_CANDIDATE_TURNS = 15


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
            # Django 5.2 tabiiy async ORM metodi — alohida sync_to_async
            # wrapper shart emas, event loop bloklanmaydi.
            vacancy = await Vacancy.objects.aget(id=self.vacancy_id)

            self.interview_engine = AIInterviewEngine(vacancy=vacancy, user=self.user)
            self.candidate_turns = 0

            initial_greeting = "Assalomu alaykum! Aceltai tizimiga xush kelibsiz. Suhbatni boshlashga tayyormisiz?"
            await self.send(text_data=json.dumps({
                'type': 'ai_message',
                'message': initial_greeting
            }))
        except Vacancy.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'error_message',
                'message': "Vakansiya topilmadi."
            }))
            await self.close(code=4004)
        except Exception as e:
            logger.error(f"WebSocket ulanish xatoligi: {str(e)}")
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
        # 1) Xabarni JSON sifatida o'qishga urinamiz. Format xato bo'lsa,
        #    butun ulanishni yopmasdan — faqat ogohlantirish yuborib,
        #    suhbatni davom ettiramiz (foydalanuvchi progressi yo'qolmasin).
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error_message',
                'message': "Xabar formati noto'g'ri. Iltimos, qaytadan yuboring."
            }))
            return

        user_message = data.get('message')
        if not user_message:
            return

        try:
            # AsyncGroq orqali to'g'ridan-to'g'ri await — endi network
            # chaqiruvi uchun database_sync_to_async ishlatilmaydi.
            ai_response = await self.interview_engine.get_next_response(user_message)
            self.candidate_turns += 1

            await self.send(text_data=json.dumps({
                'type': 'ai_message',
                'message': ai_response
            }))

            if INTERVIEW_END_MARKER in ai_response or self.candidate_turns >= MAX_CANDIDATE_TURNS:
                await self._finish_interview()

        except Exception as e:
            logger.error(f"WebSocket xabar qayta ishlash xatoligi: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error_message',
                'message': "Kechirasiz, tizimda ichki xatolik yuz berdi."
            }))
            await self.close(code=4002)

    async def _finish_interview(self):
        """
        Suhbat yakunlangach: AIEvaluator orqali baholaydi va natijani
        InterviewResult jadvaliga yozadi, so'ng ulanishni yopadi.

        Baholash/saqlashda xato yuz bersa ham, foydalanuvchiga aniq xabar
        beriladi va WebSocket toza yopiladi (server 500 bilan qulamaydi).
        """
        try:
            history = self.interview_engine.get_history()

            result = await AIEvaluator().evaluate_interview(
                vacancy=self.interview_engine.vacancy,
                chat_history=history,
            )

            await InterviewResult.objects.acreate(
                user=self.user,
                vacancy_name=str(self.vacancy_id),
                chat_log=history,
                score=result.get("score"),
                feedback=result.get("feedback"),
            )

            await self.send(text_data=json.dumps({
                'type': 'system_message',
                'message': "Suhbat muvaffaqiyatli yakunlandi. Natijalar HR panelida paydo bo'ladi."
            }))
        except Exception as e:
            logger.error(f"Intervyuni yakunlash/saqlash xatoligi: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error_message',
                'message': "Suhbat yakunlandi, lekin natijani saqlashda xatolik yuz berdi."
            }))
        finally:
            await self.close(code=1000)