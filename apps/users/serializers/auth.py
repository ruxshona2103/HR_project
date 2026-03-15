from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.users.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # super().validate tepadagi backendni ishlatadi
        data = super().validate(attrs)

        # Responsega user ma'lumotlarini qo'shish
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "phone_number": self.user.phone_number,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_staff": self.user.is_staff,
        }
        return data


class CandidateRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    auth_method = serializers.ChoiceField(choices=['phone', 'email'], write_only=True)

    class Meta:
        model = User
        fields = [
            'auth_method',
            'first_name', 'last_name', 'middle_name',
            'phone_number', 'email', 'password', 'password_confirm'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Parollar mos kelmadi"})

        auth_method = attrs.get('auth_method')

        if auth_method == 'phone' and not attrs.get('phone_number'):
            raise serializers.ValidationError(
                {"phone_number": "Telefon orqali ro'yxatdan o'tish uchun telefon raqam kiritish shart"})

        if auth_method == 'email' and not attrs.get('email'):
            raise serializers.ValidationError({"email": "Email orqali ro'yxatdan o'tish uchun email kiritish shart"})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        auth_method = validated_data.pop('auth_method')

        user = User.objects.create_user(
            email=validated_data.get('email'),
            phone_number=validated_data.get('phone_number'),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            middle_name=validated_data.get('middle_name', ''),
            user_type='candidate'
        )
        return user


class OrganizationRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    auth_method = serializers.ChoiceField(choices=['phone', 'email'], write_only=True)

    class Meta:
        model = User
        fields = [
            'auth_method',
            'organization_name', 'position',
            'first_name', 'last_name', 'middle_name',
            'phone_number', 'email', 'password', 'password_confirm'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Parollar mos kelmadi"})

        auth_method = attrs.get('auth_method')

        if auth_method == 'phone' and not attrs.get('phone_number'):
            raise serializers.ValidationError(
                {"phone_number": "Telefon orqali ro'yxatdan o'tish uchun telefon raqam kiritish shart"})

        if auth_method == 'email' and not attrs.get('email'):
            raise serializers.ValidationError({"email": "Email orqali ro'yxatdan o'tish uchun email kiritish shart"})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        auth_method = validated_data.pop('auth_method')

        user = User.objects.create_user(
            email=validated_data.get('email'),
            phone_number=validated_data.get('phone_number'),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            middle_name=validated_data.get('middle_name', ''),
            organization_name=validated_data.get('organization_name'),
            position=validated_data.get('position'),
            user_type='organization'
        )
        return user



class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, help_text="Refresh tokenni kiriting")