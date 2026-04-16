from django.urls import path
from . import views

urlpatterns = [
    path("", views.BookingListCreateView.as_view(), name="booking-list-create"),
    path("<int:pk>/", views.BookingDetailView.as_view(), name="booking-detail"),
    path("creator/", views.creator_bookings, name="creator-bookings"),
]
