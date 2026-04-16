from django.conf import settings
from django.db import models


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    language = models.CharField(max_length=50, db_index=True)
    location = models.CharField(max_length=255, db_index=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["language", "location"]),
            models.Index(fields=["starts_at", "ends_at"]),
        ]

    def __str__(self):
        return self.title


class EnrollmentStatus(models.TextChoices):
    ENROLLED = "enrolled", "Enrolled"
    CANCELED = "canceled", "Canceled"


class Enrollment(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="enrollments"
    )
    seeker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    status = models.CharField(
        max_length=10,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ENROLLED,
    )
    followup_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "seeker"],
                condition=models.Q(status="enrolled"),
                name="unique_active_enrollment",
            )
        ]
        indexes = [
            models.Index(fields=["seeker", "status"]),
            models.Index(fields=["event", "status"]),
        ]

    def __str__(self):
        return f"{self.seeker.email} → {self.event.title} ({self.status})"
