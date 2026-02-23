from .models import User, UserProfile, CandidateProfile
from rest_framework import serializers


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=13)
    code = serializers.CharField(max_length=6)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'name', 'chat_id', 'created_at']
        read_only_fields = ['phone_number', 'chat_id', 'created_at']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        # fields = "__all__"
        fields = ['id', 'first_name', 'last_name', 'birth_date', 'phone_number']

class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = ['id', 'user', 'resume', 'linkedin_url', 'github_url', 'portfolio_url', 'experience_years', 'languages']

