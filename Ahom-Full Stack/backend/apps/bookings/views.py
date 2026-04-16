from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer
from apps.sessions_app.models import Session


class BookingListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List current user's bookings, with optional ?status= and ?time= filters."""
        qs = Booking.objects.filter(user=request.user).select_related("session", "session__creator")

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        time_filter = request.query_params.get("time")
        now = timezone.now()
        if time_filter == "upcoming":
            qs = qs.filter(session__date__gte=now)
        elif time_filter == "past":
            qs = qs.filter(session__date__lt=now)

        return Response(BookingSerializer(qs, many=True).data)

    @method_decorator(ratelimit(key="user", rate="10/m", block=True))
    def post(self, request):
        """Create a booking for a session."""
        ser = BookingCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            session = Session.objects.get(pk=ser.validated_data["session_id"])
        except Session.DoesNotExist:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        if session.status != Session.Status.PUBLISHED:
            return Response({"error": "Session is not available for booking"}, status=400)

        if session.seats_available <= 0:
            return Response({"error": "No seats available"}, status=400)

        if Booking.objects.filter(user=request.user, session=session).exclude(status="cancelled").exists():
            return Response({"error": "Already booked this session"}, status=400)

        booking = Booking.objects.create(user=request.user, session=session)
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            booking = Booking.objects.select_related("session", "session__creator").get(pk=pk, user=request.user)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)
        return Response(BookingSerializer(booking).data)

    def delete(self, request, pk):
        """Cancel a booking."""
        try:
            booking = Booking.objects.get(pk=pk, user=request.user)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        if booking.status == "cancelled":
            return Response({"error": "Already cancelled"}, status=400)

        booking.status = "cancelled"
        booking.save(update_fields=["status"])
        return Response({"status": "cancelled"})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def creator_bookings(request):
    """List all bookings for sessions owned by the current creator."""
    if request.user.role != "creator":
        return Response({"error": "Creator role required"}, status=403)

    qs = (
        Booking.objects
        .filter(session__creator=request.user)
        .select_related("user", "session")
        .order_by("-created_at")
    )
    return Response(BookingSerializer(qs, many=True).data)
