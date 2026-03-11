from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from .models import TeamAbout, ContactInfo, PlatformStep, Product, PricingPlan
from .serializers import (
    TeamAboutSerializer, ContactInfoSerializer,
    PlatformStepSerializer, ProductSerializer, PricingPlanSerializer
)


class LandingPageDataView(APIView):
    """
    Landing sahifa uchun barcha ma'lumotlarni bitta so'rovda qaytaruvchi View.
    Bu frontendchilar uchun juda qulay, chunki bitta request bilan butun sahifani to'ldirish mumkin.
    """

    def get(self, request, *args, **kwargs):
        team = TeamAbout.objects.first()
        contact = ContactInfo.objects.first()

        steps = PlatformStep.objects.filter(is_active=True).order_by('step_number')
        products = Product.objects.filter(is_active=True)
        pricing = PricingPlan.objects.filter(is_active=True)


        data = {
            "team": TeamAboutSerializer(team).data if team else None,
            "how_it_works": PlatformStepSerializer(steps, many=True).data,
            "products": ProductSerializer(products, many=True).data,
            "pricing": PricingPlanSerializer(pricing, many=True).data,
            "contacts": ContactInfoSerializer(contact).data if contact else None,
        }

        return Response(data, status=status.HTTP_200_OK)


class ProductListView(generics.ListAPIView):
    """Mahsulotlar ro'yxati uchun alohida endpoint"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer


class PricingPlanListView(generics.ListAPIView):
    """Narxlar tariflari uchun alohida endpoint"""
    queryset = PricingPlan.objects.filter(is_active=True)
    serializer_class = PricingPlanSerializer


class ContactInfoView(generics.RetrieveAPIView):
    """Aloqa ma'lumotlarini olish"""
    serializer_class = ContactInfoSerializer

    def get_object(self):
        return ContactInfo.objects.first()
