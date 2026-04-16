from rest_framework import serializers
from .models import Booking
from apps.sessions_app.serializers import SessionListSerializer
from apps.accounts.serializers import UserSerializer


class BookingSerializer(serializers.ModelSerializer):
    session = SessionListSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "user", "session", "status", "payment_id", "created_at"]
        read_only_fields = ["id", "user", "status", "payment_id", "created_at"]


class BookingCreateSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
