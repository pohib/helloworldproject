from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, TelegramUser
from allauth.account.admin import EmailAddressAdmin as BaseEmailAddressAdmin

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профили'

class TelegramUserInline(admin.StackedInline):
    model = TelegramUser
    can_delete = False
    verbose_name_plural = 'Telegram Профили'
    readonly_fields = ('telegram_id', 'auth_date')

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, TelegramUserInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar_preview')
    search_fields = ('user__username', 'user__email')

    def avatar_preview(self, obj):
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" style="max-height: 50px; max-width: 50px;" />'
        return "No avatar"
    avatar_preview.allow_tags = True

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_id', 'username', 'first_name', 'last_name')
    search_fields = ('user__username', 'telegram_id', 'username')
    readonly_fields = ('auth_date',)
    


