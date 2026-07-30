from groq import Groq, AsyncGroq
from django.conf import settings
from apps.vacancies.models import Vacancy
from ..prompts.templates import (
    get_interviewer_prompt,
    get_evaluation_prompt,
    get_resume_check_prompt
)
import json
import logging

logger = logging.getLogger(__name__)

# Suhbat juda uzayib ketmasligi (token/xarajat portlashi) uchun himoya chegarasi.
# Interviewer prompt 5-7 ta savol so'rashni so'raydi, lekin AI har doim ham
# o'z vaqtida "SUHBAT YAKUNLANDI" demasligi mumkin — shu bois qo'shimcha
# xavfsizlik chegarasi sifatida saqlanadigan oxirgi xabarlar soni cheklanadi.
MAX_HISTORY_MESSAGES = 24  # ~12 savol-javob juftligi (system prompt bundan tashqari)


class BaseAIService:
    """Sinxron (WSGI/DRF view) kontekstlar uchun — masalan ResumeService."""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model_name = "llama-3.3-70b-versatile"


class AsyncBaseAIService:
    """
    Asinxron (Channels/WebSocket) kontekstlar uchun.

    MUHIM: bu servis network (Groq API) chaqiruvlarini to'g'ridan-to'g'ri
    `await` bilan bajaradi (AsyncGroq orqali) — Django Channelsning
    `database_sync_to_async`i FAQAT ma'lumotlar bazasi (ORM) operatsiyalari
    uchun mo'ljallangan bo'lib, uni tarmoq so'roviga ishlatish thread-pool
    resurslarini behuda band qiladi. Shu sabab bu klass ORM bilan ishlamaydi —
    kerakli obyektlar (`vacancy`) chaqiruvchi tomonidan (consumers.py, Django
    async ORM — `aget()`/`acreate()` orqali) tayyor holda uzatiladi.
    """

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model_name = "llama-3.3-70b-versatile"


class AIInterviewEngine(AsyncBaseAIService):
    """
    Bitta nomzod-vakansiya juftligi uchun bitta intervyu sessiyasini boshqaradi.

    `vacancy` — Vacancy modelining tayyor instansiyasi bo'lishi kerak
    (DB so'rovi consumers.py ichida `await Vacancy.objects.aget(...)` orqali
    bajariladi, shu klassning o'zi ORM bilan ishlamaydi).
    """

    def __init__(self, vacancy, user=None):
        super().__init__()
        self.vacancy = vacancy
        self.user = user
        self.system_instruction = get_interviewer_prompt(self.vacancy)

        self.system_message = {"role": "system", "content": self.system_instruction}
        self.messages = [self.system_message]
        self.history = []  # [{"role": "candidate"/"ai", "content": "..."}] — InterviewResult uchun

    def _trim_messages_if_needed(self):
        """
        Context window (token limiti/xarajat) portlab ketmasligi uchun,
        eng eski xabarlarni system prompt'dan keyin qirqib boradi.
        """
        if len(self.messages) > MAX_HISTORY_MESSAGES:
            overflow = len(self.messages) - MAX_HISTORY_MESSAGES
            self.messages = [self.system_message] + self.messages[1 + overflow:]

    async def get_next_response(self, user_text):
        try:
            self.messages.append({"role": "user", "content": user_text})
            self._trim_messages_if_needed()

            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
            )
            ai_text = completion.choices[0].message.content

            self.messages.append({"role": "assistant", "content": ai_text})
            self.history.append({"role": "candidate", "content": user_text})
            self.history.append({"role": "ai", "content": ai_text})

            return ai_text
        except Exception as e:
            logger.error(f"AI Interview xatosi: {str(e)}")
            return "Kechirasiz, tizimda xatolik yuz berdi. Qaytadan urinib ko'ring."

    def get_history(self):
        return self.history


class AIEvaluator(AsyncBaseAIService):
    """
    `vacancy` — tayyor Vacancy instansiyasi (consumers.py'dan uzatiladi).
    """

    async def evaluate_interview(self, vacancy, chat_history):
        history_text = "\n".join(
            f"{m.get('role', 'user')}: {m.get('content', '')}" for m in chat_history
        )
        prompt = get_evaluation_prompt(vacancy, history_text)

        raw_text = ""
        try:
            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            raw_text = (completion.choices[0].message.content or "").strip()

            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`")
                if raw_text.lower().startswith("json"):
                    raw_text = raw_text[4:].strip()

            data = json.loads(raw_text)

            score = data.get("score")
            try:
                score = int(score)
                score = max(1, min(100, score))
            except (TypeError, ValueError):
                score = None

            feedback = data.get("feedback") or ""
            return {"score": score, "feedback": feedback}

        except json.JSONDecodeError:
            logger.error("AI Evaluator: javobni JSON sifatida o'qib bo'lmadi: %s", raw_text[:300])
            return {"score": None, "feedback": raw_text or "Baholashda xatolik yuz berdi."}
        except Exception as e:
            logger.error(f"AI Evaluator xatosi: {str(e)}")
            return {"score": None, "feedback": "Baholashda xatolik yuz berdi."}


class ResumeService(BaseAIService):
    """
    E'tibor: bu servis SINXRON (Groq, AsyncGroq emas) — chunki u faqat
    oddiy, sinxron DRF APIView (ResumeCheckAPIView) ichidan chaqiriladi,
    Channels/async consumer ichidan emas. Shu bois sinxron client bu yerda
    to'g'ri va yetarli — hech qanday async/await muammosi yo'q.
    """

    def analyze_resume(self, resume_text, vacancy_id):
        vacancy = Vacancy.objects.get(id=vacancy_id)
        prompt = get_resume_check_prompt(vacancy, resume_text)

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            # return completion.choices[0].message.content
            raw_text = (completion.choices[0].message.content or "").strip()

            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`")
                if raw_text.lower().startswith("json"):
                    raw_text = raw_text[4:].strip()

            return raw_text
        except Exception as e:
            logger.error(f"Resume Service xatosi: {str(e)}")
            return '{"error": "AI tahlil qila olmadi"}'