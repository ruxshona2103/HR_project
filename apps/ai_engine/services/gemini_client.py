from google import genai
from django.conf import settings
from google.genai import types


class GeminiClient:
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_KEY,
            http_options=types.HttpOptions(api_version='v1')
        )
        self.model_name = "gemini-2.0-flash"

    def get_client(self):
        return self.client