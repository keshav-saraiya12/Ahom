import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("events_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "send-enrollment-followup-every-5-min": {
        "task": "events.tasks.send_enrollment_followup_emails",
        "schedule": crontab(minute="*/5"),
    },
    "send-event-reminder-every-5-min": {
        "task": "events.tasks.send_event_reminder_emails",
        "schedule": crontab(minute="*/5"),
    },
}
