from apps.user_profile.models import UserProfile
from rest_framework import serializers


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'birth_date', 'phone_number', 'university_name', 'degree', 'course', 'field_of_study']
