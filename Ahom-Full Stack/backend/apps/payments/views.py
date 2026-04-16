import stripe
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.sessions_app.models import Session
from apps.bookings.models import Booking


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_checkout(request):
    """Create a Stripe Checkout Session for booking a session."""
    if not settings.STRIPE_SECRET_KEY:
        return Response({"error": "Stripe is not configured"}, status=501)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session_id = request.data.get("session_id")

    try:
        session_obj = Session.objects.get(pk=session_id, status="published")
    except Session.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

    if session_obj.seats_available <= 0:
        return Response({"error": "No seats available"}, status=400)

    if session_obj.price <= 0:
        booking = Booking.objects.create(user=request.user, session=session_obj)
        return Response({"booking_id": booking.id, "free": True})

    origin = request.headers.get("Origin", "http://localhost")
    checkout = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": session_obj.title},
                "unit_amount": int(session_obj.price * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{origin}/booking/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{origin}/sessions/{session_obj.id}",
        metadata={
            "user_id": str(request.user.id),
            "session_id": str(session_obj.id),
        },
    )
    return Response({"checkout_url": checkout.url, "checkout_id": checkout.id})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        return Response(status=501)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return Response(status=400)

    if event["type"] == "checkout.session.completed":
        data = event["data"]["object"]
        meta = data.get("metadata", {})
        user_id = meta.get("user_id")
        session_id = meta.get("session_id")

        if user_id and session_id:
            booking, _ = Booking.objects.get_or_create(
                user_id=user_id,
                session_id=session_id,
                defaults={"status": "confirmed", "payment_id": data["id"]},
            )
            if not booking.payment_id:
                booking.payment_id = data["id"]
                booking.status = "confirmed"
                booking.save(update_fields=["payment_id", "status"])

    return Response({"received": True})
