from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "oauth_provider", "is_active"]
    list_filter = ["role", "oauth_provider", "is_active"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Extra", {"fields": ("role", "avatar", "bio", "oauth_provider", "oauth_uid")}),
    )
