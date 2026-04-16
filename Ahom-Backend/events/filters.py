import django_filters
from django.db.models import Q

from .models import Event


class EventFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(lookup_expr="icontains")
    language = django_filters.CharFilter(lookup_expr="iexact")
    starts_after = django_filters.DateTimeFilter(field_name="starts_at", lookup_expr="gte")
    starts_before = django_filters.DateTimeFilter(field_name="starts_at", lookup_expr="lte")
    q = django_filters.CharFilter(method="search_title_description")

    class Meta:
        model = Event
        fields = ["location", "language", "starts_after", "starts_before", "q"]

    def search_title_description(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )
