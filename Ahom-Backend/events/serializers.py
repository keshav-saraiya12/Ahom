from django.utils import timezone
from rest_framework import serializers

from .models import Enrollment, EnrollmentStatus, Event


class EventSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    available_seats = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "language",
            "location",
            "starts_at",
            "ends_at",
            "capacity",
            "created_by",
            "created_by_email",
            "enrolled_count",
            "available_seats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_available_seats(self, obj):
        if obj.capacity is None:
            return None
        enrolled = getattr(obj, "enrolled_count", None)
        if enrolled is None:
            enrolled = obj.enrollments.filter(status=EnrollmentStatus.ENROLLED).count()
        return max(obj.capacity - enrolled, 0)

    def validate(self, data):
        starts_at = data.get("starts_at") or (self.instance and self.instance.starts_at)
        ends_at = data.get("ends_at") or (self.instance and self.instance.ends_at)
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End time must be after start time."}
            )
        return data


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "language",
            "location",
            "starts_at",
            "ends_at",
            "capacity",
        ]

    def validate(self, data):
        if data.get("ends_at") and data.get("starts_at"):
            if data["ends_at"] <= data["starts_at"]:
                raise serializers.ValidationError(
                    {"ends_at": "End time must be after start time."}
                )
        return data


class EnrollmentSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source="event.title", read_only=True)
    seeker_email = serializers.EmailField(source="seeker.email", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "event",
            "event_title",
            "seeker",
            "seeker_email",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "seeker", "status", "created_at", "updated_at"]


class EnrollRequestSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
