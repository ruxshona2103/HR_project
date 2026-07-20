import google.generativeai as genai
from django.conf import settings


class GeminiClient:
    def __init__(self):
        # API kalitni settings'dan olamiz
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-1.5-flash"

    def get_model(self, system_instruction=None):
        return genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )