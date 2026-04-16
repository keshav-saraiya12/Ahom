from django.db import IntegrityError
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsEmailVerified, IsFacilitator, IsSeeker

from .filters import EventFilter
from .models import Enrollment, EnrollmentStatus, Event
from .serializers import (
    EnrollmentSerializer,
    EnrollRequestSerializer,
    EventCreateSerializer,
    EventSerializer,
)


# ---------------------------------------------------------------------------
# Seeker endpoints
# ---------------------------------------------------------------------------


class EventSearchView(generics.ListAPIView):
    """
    GET /api/events/search/
    Searchable, filterable list of upcoming events for seekers.
    """

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified]
    filterset_class = EventFilter
    search_fields = ["title", "description"]
    ordering_fields = ["starts_at", "created_at"]
    ordering = ["starts_at"]

    def get_queryset(self):
        return (
            Event.objects.filter(starts_at__gte=timezone.now())
            .select_related("created_by")
            .annotate(
                enrolled_count=Count(
                    "enrollments",
                    filter=Q(enrollments__status=EnrollmentStatus.ENROLLED),
                )
            )
        )


class EnrollView(APIView):
    """POST /api/enrollments/enroll/"""

    permission_classes = [IsAuthenticated, IsEmailVerified, IsSeeker]

    def post(self, request):
        ser = EnrollRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            event = Event.objects.annotate(
                enrolled_count=Count(
                    "enrollments",
                    filter=Q(enrollments__status=EnrollmentStatus.ENROLLED),
                )
            ).get(id=ser.validated_data["event_id"])
        except Event.DoesNotExist:
            return Response(
                {"detail": "Event not found.", "code": "event_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if event.starts_at <= timezone.now():
            return Response(
                {"detail": "Cannot enroll in a past or ongoing event.", "code": "event_started"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if event.capacity is not None and event.enrolled_count >= event.capacity:
            return Response(
                {"detail": "Event is at full capacity.", "code": "event_full"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            enrollment = Enrollment.objects.create(
                event=event, seeker=request.user, status=EnrollmentStatus.ENROLLED
            )
        except IntegrityError:
            return Response(
                {"detail": "You are already enrolled in this event.", "code": "already_enrolled"},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED
        )


class CancelEnrollmentView(APIView):
    """POST /api/enrollments/<id>/cancel/"""

    permission_classes = [IsAuthenticated, IsEmailVerified, IsSeeker]

    def post(self, request, pk):
        try:
            enrollment = Enrollment.objects.get(
                pk=pk, seeker=request.user, status=EnrollmentStatus.ENROLLED
            )
        except Enrollment.DoesNotExist:
            return Response(
                {"detail": "Active enrollment not found.", "code": "enrollment_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        enrollment.status = EnrollmentStatus.CANCELED
        enrollment.save(update_fields=["status", "updated_at"])
        return Response(EnrollmentSerializer(enrollment).data)


class PastEnrollmentsView(generics.ListAPIView):
    """GET /api/enrollments/past/"""

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSeeker]

    def get_queryset(self):
        return (
            Enrollment.objects.filter(
                seeker=self.request.user,
                status=EnrollmentStatus.ENROLLED,
                event__ends_at__lt=timezone.now(),
            )
            .select_related("event", "seeker")
            .order_by("-event__ends_at")
        )


class UpcomingEnrollmentsView(generics.ListAPIView):
    """GET /api/enrollments/upcoming/"""

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSeeker]

    def get_queryset(self):
        return (
            Enrollment.objects.filter(
                seeker=self.request.user,
                status=EnrollmentStatus.ENROLLED,
                event__starts_at__gte=timezone.now(),
            )
            .select_related("event", "seeker")
            .order_by("event__starts_at")
        )


# ---------------------------------------------------------------------------
# Facilitator endpoints
# ---------------------------------------------------------------------------


class FacilitatorEventListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/facilitator/events/  — list my events with enrollment counts.
    POST /api/facilitator/events/  — create an event.
    """

    permission_classes = [IsAuthenticated, IsEmailVerified, IsFacilitator]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EventCreateSerializer
        return EventSerializer

    def get_queryset(self):
        return (
            Event.objects.filter(created_by=self.request.user)
            .annotate(
                enrolled_count=Count(
                    "enrollments",
                    filter=Q(enrollments__status=EnrollmentStatus.ENROLLED),
                )
            )
            .select_related("created_by")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        self.perform_create(ser)
        # Return full representation
        event = (
            Event.objects.filter(pk=ser.instance.pk)
            .annotate(
                enrolled_count=Count(
                    "enrollments",
                    filter=Q(enrollments__status=EnrollmentStatus.ENROLLED),
                )
            )
            .select_related("created_by")
            .first()
        )
        return Response(
            EventSerializer(event).data, status=status.HTTP_201_CREATED
        )


class FacilitatorEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/facilitator/events/<id>/
    PUT    /api/facilitator/events/<id>/
    PATCH  /api/facilitator/events/<id>/
    DELETE /api/facilitator/events/<id>/
    Only the creator may modify.
    """

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified, IsFacilitator]

    def get_queryset(self):
        return (
            Event.objects.filter(created_by=self.request.user)
            .annotate(
                enrolled_count=Count(
                    "enrollments",
                    filter=Q(enrollments__status=EnrollmentStatus.ENROLLED),
                )
            )
            .select_related("created_by")
        )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return EventCreateSerializer
        return EventSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        ser = EventCreateSerializer(instance, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        ser.save()
        # Return full representation
        event = (
            Event.objects.filter(pk=instance.pk)
            .annotate(
                enrolled_count=Count(
                    "enrollments",
                    filter=Q(enrollments__status=EnrollmentStatus.ENROLLED),
                )
            )
            .select_related("created_by")
            .first()
        )
        return Response(EventSerializer(event).data)
