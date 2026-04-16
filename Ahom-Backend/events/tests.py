from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import RoleChoices, UserProfile

from .models import Enrollment, EnrollmentStatus, Event

User = get_user_model()


class EventTestMixin:
    """Shared helpers for event tests."""

    def _make_user(self, email, role, verified=True):
        user = User.objects.create_user(username=email, email=email, password="StrongP@ss1")
        UserProfile.objects.create(user=user, role=role, is_email_verified=verified)
        return user

    def _auth(self, client, email):
        resp = client.post(
            "/auth/login/", {"email": email, "password": "StrongP@ss1"}, format="json"
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    def _make_event(self, facilitator, **overrides):
        defaults = {
            "title": "Test Event",
            "description": "A test event.",
            "language": "English",
            "location": "Online",
            "starts_at": timezone.now() + timedelta(days=1),
            "ends_at": timezone.now() + timedelta(days=1, hours=2),
            "capacity": 10,
            "created_by": facilitator,
        }
        defaults.update(overrides)
        return Event.objects.create(**defaults)


class SeekerTests(EventTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seeker = self._make_user("seeker@test.com", RoleChoices.SEEKER)
        self.facilitator = self._make_user("fac@test.com", RoleChoices.FACILITATOR)
        self._auth(self.client, "seeker@test.com")

    def test_search_events(self):
        self._make_event(self.facilitator)
        self._make_event(self.facilitator, title="Hindi Workshop", language="Hindi")
        resp = self.client.get("/api/events/search/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_search_filter_language(self):
        self._make_event(self.facilitator, language="Hindi")
        self._make_event(self.facilitator, language="English")
        resp = self.client.get("/api/events/search/?language=Hindi")
        self.assertEqual(resp.data["count"], 1)

    def test_search_filter_q(self):
        self._make_event(self.facilitator, title="Python Bootcamp")
        self._make_event(self.facilitator, title="Yoga Class")
        resp = self.client.get("/api/events/search/?q=python")
        self.assertEqual(resp.data["count"], 1)

    def test_enroll_success(self):
        event = self._make_event(self.facilitator)
        resp = self.client.post(
            "/api/enrollments/enroll/", {"event_id": event.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "enrolled")

    def test_enroll_duplicate_blocked(self):
        event = self._make_event(self.facilitator)
        self.client.post("/api/enrollments/enroll/", {"event_id": event.id}, format="json")
        resp = self.client.post(
            "/api/enrollments/enroll/", {"event_id": event.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_enroll_full_capacity(self):
        event = self._make_event(self.facilitator, capacity=1)
        other_seeker = self._make_user("other@test.com", RoleChoices.SEEKER)
        Enrollment.objects.create(
            event=event, seeker=other_seeker, status=EnrollmentStatus.ENROLLED
        )
        resp = self.client.post(
            "/api/enrollments/enroll/", {"event_id": event.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["code"], "event_full")

    def test_cancel_enrollment(self):
        event = self._make_event(self.facilitator)
        enroll_resp = self.client.post(
            "/api/enrollments/enroll/", {"event_id": event.id}, format="json"
        )
        resp = self.client.post(f"/api/enrollments/{enroll_resp.data['id']}/cancel/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "canceled")

    def test_upcoming_enrollments(self):
        event = self._make_event(self.facilitator)
        Enrollment.objects.create(
            event=event, seeker=self.seeker, status=EnrollmentStatus.ENROLLED
        )
        resp = self.client.get("/api/enrollments/upcoming/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_past_enrollments(self):
        event = self._make_event(
            self.facilitator,
            starts_at=timezone.now() - timedelta(days=2),
            ends_at=timezone.now() - timedelta(days=1),
        )
        Enrollment.objects.create(
            event=event, seeker=self.seeker, status=EnrollmentStatus.ENROLLED
        )
        resp = self.client.get("/api/enrollments/past/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)


class FacilitatorTests(EventTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.facilitator = self._make_user("fac@test.com", RoleChoices.FACILITATOR)
        self._auth(self.client, "fac@test.com")

    def test_create_event(self):
        resp = self.client.post(
            "/api/facilitator/events/",
            {
                "title": "Django Workshop",
                "description": "Learn Django",
                "language": "English",
                "location": "Online",
                "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
                "ends_at": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
                "capacity": 50,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["title"], "Django Workshop")

    def test_list_my_events(self):
        self._make_event(self.facilitator)
        resp = self.client.get("/api/facilitator/events/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_update_event(self):
        event = self._make_event(self.facilitator)
        resp = self.client.patch(
            f"/api/facilitator/events/{event.id}/",
            {"title": "Updated Title"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "Updated Title")

    def test_delete_event(self):
        event = self._make_event(self.facilitator)
        resp = self.client.delete(f"/api/facilitator/events/{event.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_cannot_update_others_event(self):
        other = self._make_user("other_fac@test.com", RoleChoices.FACILITATOR)
        event = self._make_event(other)
        resp = self.client.patch(
            f"/api/facilitator/events/{event.id}/",
            {"title": "Hacked"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_event_enrollment_counts(self):
        event = self._make_event(self.facilitator, capacity=10)
        seeker = self._make_user("s@test.com", RoleChoices.SEEKER)
        Enrollment.objects.create(
            event=event, seeker=seeker, status=EnrollmentStatus.ENROLLED
        )
        resp = self.client.get("/api/facilitator/events/")
        self.assertEqual(resp.data["results"][0]["enrolled_count"], 1)
        self.assertEqual(resp.data["results"][0]["available_seats"], 9)


class RBACTests(EventTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_seeker_cannot_create_event(self):
        seeker = self._make_user("seeker_rbac@test.com", RoleChoices.SEEKER)
        self._auth(self.client, "seeker_rbac@test.com")
        resp = self.client.post(
            "/api/facilitator/events/",
            {
                "title": "Nope",
                "language": "English",
                "location": "Online",
                "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
                "ends_at": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_facilitator_cannot_enroll(self):
        fac = self._make_user("fac_rbac@test.com", RoleChoices.FACILITATOR)
        self._auth(self.client, "fac_rbac@test.com")
        event = self._make_event(fac)
        resp = self.client.post(
            "/api/enrollments/enroll/", {"event_id": event.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unverified_user_blocked(self):
        self._make_user("unver@test.com", RoleChoices.SEEKER, verified=False)
        # Login manually since unverified can't use login endpoint
        user = User.objects.get(email="unver@test.com")
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}"
        )
        resp = self.client.get("/api/events/search/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
