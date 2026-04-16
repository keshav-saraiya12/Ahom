from django.contrib import admin
from .models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["title", "creator", "date", "price", "max_seats", "status"]
    list_filter = ["status", "date"]
    search_fields = ["title", "description"]
