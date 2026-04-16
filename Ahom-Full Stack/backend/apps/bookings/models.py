from django.db import models
from django.conf import settings


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        PENDING = "pending", "Pending"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    session = models.ForeignKey(
        "sessions_app.Session",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED)
    payment_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "session"],
                name="unique_booking_per_session",
                condition=~models.Q(status="cancelled"),
            )
        ]

    def __str__(self):
        return f"{self.user.username} → {self.session.title}"
