from django.db import models
from django.conf import settings


class Session(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_sessions",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    image_url = models.URLField(blank=True, default="")
    date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    max_seats = models.PositiveIntegerField(default=20)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PUBLISHED)
    tags = models.CharField(max_length=500, blank=True, default="")
    location = models.CharField(max_length=300, blank=True, default="Online")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title

    @property
    def seats_booked(self):
        return self.bookings.exclude(status="cancelled").count()

    @property
    def seats_available(self):
        return max(0, self.max_seats - self.seats_booked)
