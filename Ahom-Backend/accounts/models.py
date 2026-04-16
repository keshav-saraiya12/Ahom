import random
import string

from django.conf import settings
from django.db import models
from django.utils import timezone


class RoleChoices(models.TextChoices):
    SEEKER = "seeker", "Seeker"
    FACILITATOR = "facilitator", "Facilitator"


class UserProfile(models.Model):
    """
    Extends the default Django User with role and email-verification state.
    Uses a OneToOne link so we never touch AUTH_USER_MODEL.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    is_email_verified = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["role"])]

    def __str__(self):
        return f"{self.user.email} ({self.role})"


class EmailOTP(models.Model):
    """Stores a 6-digit OTP for email verification with TTL and attempt cap."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otps"
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"OTP for {self.user.email}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @classmethod
    def generate(cls, user):
        code = "".join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timezone.timedelta(
            seconds=settings.OTP_EXPIRY_SECONDS
        )
        return cls.objects.create(user=user, code=code, expires_at=expires_at)
