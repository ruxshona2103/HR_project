from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users1.models import User, OTPCode, PendingRegistration, OTPAttempt, EmailVerificationCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'email', 'phone_number', 'user_type', 'is_active', 'is_staff', 'created_at')
    list_filter = ('user_type', 'is_active', 'is_staff')
    search_fields = ('email', 'phone_number', 'first_name', 'last_name', 'organization_name')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        ('Shaxsiy ma\'lumotlar', {'fields': ('first_name', 'last_name', 'middle_name')}),
        ('Tashkilot', {'fields': ('organization_name', 'position')}),
        ('Telegram', {'fields': ('chat_id',)}),
        ('Ruxsatlar', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2', 'user_type'),
        }),
    )


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'is_used', 'created_at')
    list_filter = ('is_used',)
    search_fields = ('phone_number',)
    ordering = ('-created_at',)


@admin.register(PendingRegistration)
class PendingRegistrationAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user_type', 'first_name', 'last_name', 'created_at')
    list_filter = ('user_type',)
    search_fields = ('phone_number', 'first_name', 'last_name')
    ordering = ('-created_at',)


@admin.register(OTPAttempt)
class OTPAttemptAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'attempts', 'blocked_until', 'last_attempt')
    search_fields = ('phone_number',)
    ordering = ('-last_attempt',)


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'user_type', 'is_used', 'created_at')
    list_filter = ('user_type', 'is_used')
    search_fields = ('email',)
    ordering = ('-created_at',)
