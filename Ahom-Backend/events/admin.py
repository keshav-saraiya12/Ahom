from django.contrib import admin

from .models import Enrollment, Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "location", "starts_at", "ends_at", "capacity", "created_by")
    list_filter = ("language", "location")
    search_fields = ("title", "description")
    date_hierarchy = "starts_at"


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("seeker", "event", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("seeker__email", "event__title")
