from .models import User
from rest_framework import serializers


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=13)
    code = serializers.CharField(max_length=6)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'name', 'chat_id', 'created_at']
        read_only_fields = ['phone_number', 'chat_id', 'created_at']
