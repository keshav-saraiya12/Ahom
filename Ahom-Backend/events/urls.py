from django.urls import path

from . import views

urlpatterns = [
    # Seeker
    path("events/search/", views.EventSearchView.as_view(), name="event-search"),
    path("enrollments/enroll/", views.EnrollView.as_view(), name="enroll"),
    path(
        "enrollments/<int:pk>/cancel/",
        views.CancelEnrollmentView.as_view(),
        name="cancel-enrollment",
    ),
    path(
        "enrollments/past/",
        views.PastEnrollmentsView.as_view(),
        name="past-enrollments",
    ),
    path(
        "enrollments/upcoming/",
        views.UpcomingEnrollmentsView.as_view(),
        name="upcoming-enrollments",
    ),
    # Facilitator
    path(
        "facilitator/events/",
        views.FacilitatorEventListCreateView.as_view(),
        name="facilitator-events",
    ),
    path(
        "facilitator/events/<int:pk>/",
        views.FacilitatorEventDetailView.as_view(),
        name="facilitator-event-detail",
    ),
]
