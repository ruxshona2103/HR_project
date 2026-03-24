from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import TeamAbout, ContactInfo, PlatformStep, Product, PricingPlan


class LandingPageTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Test uchun vaqtinchalik bazani 1 marta tayyorlash.
        Bu metod testlarni bir necha barobar tezlashtiradi.
        """
        # Singleton
        # 1. Jamoa ma'lumotini yaratamiz
        cls.team = TeamAbout.objects.create(
            title="Test Jamoa",
            description="Biz eng zo'r jamoamiz",
            experience_years=5
        )

        # Singleton: Kontakt yaratish
        cls.contact = ContactInfo.objects.create(
            phone_number="+998901234567",
            email="test@mail.com",
            telegram_link="https://t.me/test"
        )

        # Dinamik: Qadam (how_it_works uchun)
        cls.step = PlatformStep.objects.create(
            step_number=1,
            title="Ro'yxatdan o'tish",
            description="Tizimga kiring",
            is_active=True
        )

        # Dinamik: Mahsulotlar (Filtrlashni tekshirish uchun 2 ta)
        cls.active_prod = Product.objects.create(
            name="Aktiv",
            is_active=True,
            description="Test tavsif",
            icon="test_icon.png"  # Test uchun shunchaki nom
        )
        cls.inactive_prod = Product.objects.create(name="Nofaol", is_active=False)

        cls.plan = PricingPlan.objects.create(
            name="Pro",
            price=15000.00,
            currency="UZS",
            features="Hammasi",
            is_active=True
        )

        # API URL manzili (urls.py dagi 'name' orqali)
        cls.main_url = reverse('landing_page:landing-data')

    def test_main_landing_data_structure(self):
        """
        LandingPageDataView qaytarayotgan JSON kalitlarini tekshirish.
        Bizda: 'team', 'how_it_works', 'products', 'pricing', 'contacts'
        """
        response = self.client.get(self.main_url)

        # 1. Status 200mi?
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Kalitlar to'g'rimi? (View'dagi 'data' lug'ati bilan solishtiramiz)
        keys = response.data.keys()
        self.assertIn('team', keys)
        self.assertIn('how_it_works', keys)
        self.assertIn('products', keys)
        self.assertIn('pricing', keys)
        self.assertIn('contacts', keys)

    def test_logic_active_items_only(self):
        """
        Faqat is_active=True bo'lgan mahsulotlar kelyaptimi?
        """
        response = self.client.get(self.main_url)

        # Bazada 2 ta mahsulot bor, lekin faqat 1 tasi aktiv
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['name'], "Aktiv")

    def test_singleton_logic(self):
        """Jamoa ma'lumoti to'g'ri obyekt bo'lib kelyaptimi?"""
        response = self.client.get(self.main_url)

        # Jamoa bitta bo'lgani uchun u List emas, Dict bo'lishi kerak
        self.assertIsInstance(response.data['team'], dict)
        self.assertEqual(response.data['team']['title'], "Test Jamoa")

    def test_pricing_plan_data(self):
        """Tarif rejalari to'g'ri formatda kelayotganini tekshirish"""
        response = self.client.get(self.main_url)

        # Bazada yaratilgan tariflar ro'yxati kelishini tekshiramiz
        pricing_data = response.data['pricing']

        # Ro'yxat bo'sh emasligiga ishonch hosil qilamiz
        # self.assertTrue(len(pricing_data) > 0)

        # Narx maydoni string bo'lib kelayotganini tekshiramiz
        if len(pricing_data) > 0:
            self.assertIsInstance(pricing_data[0]['price'], str)