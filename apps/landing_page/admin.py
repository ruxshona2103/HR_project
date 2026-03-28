from django.contrib import admin

from .models import TeamAbout, ContactInfo, PlatformStep, Product, PricingPlan



class SingletonAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TeamAbout)
class TeamAboutAdmin(SingletonAdmin):
    list_display = ('title', 'description', 'experience_years')


@admin.register(ContactInfo)
class ContactInfoAdmin(SingletonAdmin):
    list_display = ('email', 'phone_number')


    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('phone_number', 'email')
        }),
        ("Ijtimoiy tarmoqlar", {
            'fields': ('telegram_link', 'instagram_link'),
            'description': "Iltimos, to'liq URL manzilini kiriting (masalan: https://t.me/...)"
        }),
    )


@admin.register(PlatformStep)
class PlatformStepAdmin(admin.ModelAdmin):
    list_display = ('step_number', 'title', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('title', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'currency')
