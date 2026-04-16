"""Celery tasks for scheduled emails."""
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Enrollment, EnrollmentStatus


@shared_task
def send_enrollment_followup_emails():
    """
    Send a follow-up email to seekers who enrolled exactly ~1 hour ago
    (checks a window to avoid missing any due to schedule drift).
    """
    now = timezone.now()
    window_start = now - timedelta(hours=1, minutes=5)
    window_end = now - timedelta(minutes=55)

    enrollments = Enrollment.objects.filter(
        status=EnrollmentStatus.ENROLLED,
        followup_sent=False,
        created_at__gte=window_start,
        created_at__lte=window_end,
    ).select_related("seeker", "event")

    for enrollment in enrollments:
        send_mail(
            subject=f"Thanks for enrolling in {enrollment.event.title}!",
            message=(
                f"Hi {enrollment.seeker.email},\n\n"
                f"Thanks for enrolling in \"{enrollment.event.title}\".\n"
                f"It starts at {enrollment.event.starts_at:%Y-%m-%d %H:%M} UTC.\n\n"
                f"See you there!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[enrollment.seeker.email],
            fail_silently=True,
        )
        enrollment.followup_sent = True
        enrollment.save(update_fields=["followup_sent"])


@shared_task
def send_event_reminder_emails():
    """
    Send a reminder email to seekers 1 hour before their enrolled event goes live.
    """
    now = timezone.now()
    window_start = now + timedelta(minutes=55)
    window_end = now + timedelta(hours=1, minutes=5)

    enrollments = Enrollment.objects.filter(
        status=EnrollmentStatus.ENROLLED,
        reminder_sent=False,
        event__starts_at__gte=window_start,
        event__starts_at__lte=window_end,
    ).select_related("seeker", "event")

    for enrollment in enrollments:
        send_mail(
            subject=f"Reminder: {enrollment.event.title} starts in 1 hour!",
            message=(
                f"Hi {enrollment.seeker.email},\n\n"
                f"\"{enrollment.event.title}\" is starting at "
                f"{enrollment.event.starts_at:%Y-%m-%d %H:%M} UTC — that's in about 1 hour.\n\n"
                f"Don't miss it!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[enrollment.seeker.email],
            fail_silently=True,
        )
        enrollment.reminder_sent = True
        enrollment.save(update_fields=["reminder_sent"])
