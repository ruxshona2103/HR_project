from rest_framework import serializers
from .models import TeamAbout, ContactInfo, PlatformStep, Product, PricingPlan


class TeamAboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamAbout

        fields = ['title', 'description', 'experience_years', 'team_photo']


class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = [
            'phone_number', 'email',
            'telegram_link', 'instagram_link'
        ]


class PlatformStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformStep
        fields = ['step_number', 'title', 'description']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'icon']


class PricingPlanSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)

    class Meta:
        model = PricingPlan
        fields = ['id', 'name', 'price', 'currency', 'features']
