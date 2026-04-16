from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Session
from .serializers import SessionListSerializer, SessionCreateSerializer
from .permissions import IsCreatorOrReadOnly


class SessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCreatorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "tags", "location"]
    ordering_fields = ["date", "price", "created_at"]

    def get_queryset(self):
        qs = Session.objects.select_related("creator")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        upcoming = self.request.query_params.get("upcoming")
        if upcoming == "true":
            qs = qs.filter(date__gte=timezone.now())

        creator_id = self.request.query_params.get("creator")
        if creator_id:
            qs = qs.filter(creator_id=creator_id)

        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return SessionCreateSerializer
        return SessionListSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=False, methods=["get"], url_path="mine")
    def my_sessions(self, request):
        """Return sessions created by the current user."""
        qs = self.get_queryset().filter(creator=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(SessionListSerializer(page, many=True).data)
        return Response(SessionListSerializer(qs, many=True).data)
