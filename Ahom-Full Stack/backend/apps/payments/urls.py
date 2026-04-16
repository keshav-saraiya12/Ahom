from django.urls import path
from . import views

urlpatterns = [
    path("checkout/", views.create_checkout, name="create-checkout"),
    path("webhook/", views.stripe_webhook, name="stripe-webhook"),
]
