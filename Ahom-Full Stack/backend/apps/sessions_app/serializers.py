from rest_framework import serializers
from .models import Session
from apps.accounts.serializers import UserSerializer


class SessionListSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    seats_available = serializers.IntegerField(read_only=True)
    seats_booked = serializers.IntegerField(read_only=True)

    class Meta:
        model = Session
        fields = [
            "id", "title", "description", "image_url", "date",
            "duration_minutes", "max_seats", "price", "status",
            "tags", "location", "creator", "seats_available",
            "seats_booked", "created_at",
        ]


class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            "title", "description", "image_url", "date",
            "duration_minutes", "max_seats", "price", "status",
            "tags", "location",
        ]

    def validate(self, attrs):
        if attrs.get("max_seats", 1) < 1:
            raise serializers.ValidationError({"max_seats": "Must be at least 1."})
        return attrs
