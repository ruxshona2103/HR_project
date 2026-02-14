from django.test import TestCase
from django.contrib.auth import get_user_model # <--- MUHIM: Yangi modelni olish uchun
from .models import Skill

User = get_user_model() # <--- Loyihada qaysi User model bo'lsa, shuni oladi

class SkillModelTest(TestCase):
    def test_skill_creation(self):
        # Endi bu yerda xato bo'lmaydi
        user = User.objects.create(username="testuser")
        skill = Skill.objects.create(user=user, name="Python", level="Senior")
        self.assertEqual(skill.name, "Python")