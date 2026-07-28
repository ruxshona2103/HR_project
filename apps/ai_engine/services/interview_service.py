from google import genai
from django.conf import settings
from apps.vacancies.models import Vacancy
from ..prompts.templates import (
    get_interviewer_prompt,
    get_evaluation_prompt,
    get_resume_check_prompt
)
from google.genai import types
import json
import logging

logger = logging.getLogger(__name__)


class BaseAIService:
    """DRY tamoyili uchun umumiy bazaviy AI xizmati klassi."""

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_KEY,
            http_options=types.HttpOptions(api_version='v1')
        )
        self.model_name = "gemini-2.0-flash"


class AIInterviewEngine(BaseAIService):
    """
    Bitta nomzod-vakansiya juftligi uchun bitta intervyu sessiyasini boshqaradi.

    Suhbat tarixi (`self.history`) shu instance ichida saqlanadi va intervyu
    yakunlangach `AIEvaluator.evaluate_interview()`ga uzatiladi — shu orqali
    yakuniy ball/xulosa hisoblanib, InterviewResult jadvaliga yoziladi.
    """

    def __init__(self, vacancy_id, user=None):
        super().__init__()
        self.vacancy_id = vacancy_id
        self.user = user
        self.vacancy = Vacancy.objects.get(id=vacancy_id)
        self.system_instruction = get_interviewer_prompt(self.vacancy)

        self.chat = self.client.chats.create(
            model=self.model_name,
            config={'system_instruction': self.system_instruction}
        )
        self.history = []  # [{"role": "candidate"/"ai", "content": "..."}]

    def get_next_response(self, user_text):
        try:
            response = self.chat.send_message(user_text)
            ai_text = response.text

            self.history.append({"role": "candidate", "content": user_text})
            self.history.append({"role": "ai", "content": ai_text})

            return ai_text
        except Exception as e:
            logger.error(f"AI Interview xatosi: {str(e)}")
            return "Kechirasiz, tizimda xatolik yuz berdi. Qaytadan urinib ko'ring."

    def get_history(self):
        """Baholash (AIEvaluator) uchun to'liq suhbat tarixini qaytaradi."""
        return self.history


class AIEvaluator(BaseAIService):
    """
    Yakunlangan intervyu suhbatini AI orqali baholaydi.

    Natija har doim {"score": int|None, "feedback": str} shaklida qaytadi —
    shunda chaqiruvchi kod (masalan consumers.py) natijani to'g'ridan-to'g'ri
    InterviewResult.score / InterviewResult.feedback maydonlariga yoza oladi.
    """

    def evaluate_interview(self, vacancy_id, chat_history):
        vacancy = Vacancy.objects.get(id=vacancy_id)
        history_text = "\n".join(
            f"{m.get('role', 'user')}: {m.get('content', '')}" for m in chat_history
        )
        prompt = get_evaluation_prompt(vacancy, history_text)

        raw_text = ""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            raw_text = (response.text or "").strip()

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