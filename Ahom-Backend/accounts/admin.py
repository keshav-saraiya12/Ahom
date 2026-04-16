from django.contrib import admin

from .models import EmailOTP, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_email_verified")
    list_filter = ("role", "is_email_verified")
    search_fields = ("user__email",)


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "expires_at", "is_used", "attempts")
    list_filter = ("is_used",)
