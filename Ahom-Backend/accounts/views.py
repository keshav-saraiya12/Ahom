from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailOTP, UserProfile
from .serializers import (
    LoginSerializer,
    SignupSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = SignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"]
        password = ser.validated_data["password"]
        role = ser.validated_data["role"]

        # username is required by default User; use email as username internally
        user = User.objects.create_user(
            username=email, email=email, password=password, is_active=True
        )
        UserProfile.objects.create(user=user, role=role, is_email_verified=False)

        otp = EmailOTP.generate(user)
        _send_otp_email(email, otp.code)

        return Response(
            {"detail": "Account created. Check your email for the OTP.", "code": "otp_sent"},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = VerifyEmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"].lower()
        otp_code = ser.validated_data["otp"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No account with this email.", "code": "user_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.profile.is_email_verified:
            return Response(
                {"detail": "Email already verified.", "code": "already_verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = (
            EmailOTP.objects.filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if otp is None:
            return Response(
                {"detail": "No active OTP. Request a new one.", "code": "otp_not_found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.is_expired:
            return Response(
                {"detail": "OTP has expired. Request a new one.", "code": "otp_expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            return Response(
                {"detail": "Too many attempts. Request a new OTP.", "code": "otp_max_attempts"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp.attempts += 1
        otp.save(update_fields=["attempts"])

        if otp.code != otp_code:
            remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
            return Response(
                {
                    "detail": f"Invalid OTP. {remaining} attempt(s) remaining.",
                    "code": "otp_invalid",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user.profile.is_email_verified = True
        user.profile.save(update_fields=["is_email_verified"])

        return Response(
            {"detail": "Email verified successfully.", "code": "email_verified"},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"].lower()
        password = ser.validated_data["password"]

        try:
            user = User.objects.select_related("profile").get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid credentials.", "code": "invalid_credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Invalid credentials.", "code": "invalid_credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.profile.is_email_verified:
            return Response(
                {"detail": "Email is not verified. Please verify first.", "code": "email_not_verified"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response(
                {"detail": "Refresh token is required.", "code": "token_required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            old_refresh = RefreshToken(token)
            new_refresh = RefreshToken.for_user(
                User.objects.get(id=old_refresh["user_id"])
            )
            old_refresh.blacklist()
        except Exception:
            try:
                old_refresh = RefreshToken(token)
                user = User.objects.get(id=old_refresh["user_id"])
                new_refresh = RefreshToken.for_user(user)
            except Exception:
                return Response(
                    {"detail": "Invalid or expired refresh token.", "code": "token_invalid"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        return Response(
            {
                "access": str(new_refresh.access_token),
                "refresh": str(new_refresh),
            },
            status=status.HTTP_200_OK,
        )


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").lower()
        if not email:
            return Response(
                {"detail": "Email is required.", "code": "email_required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.select_related("profile").get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No account with this email.", "code": "user_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.profile.is_email_verified:
            return Response(
                {"detail": "Email already verified.", "code": "already_verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = EmailOTP.generate(user)
        _send_otp_email(email, otp.code)

        return Response(
            {"detail": "OTP resent to your email.", "code": "otp_sent"},
            status=status.HTTP_200_OK,
        )


def _send_otp_email(email, code):
    send_mail(
        subject="Your Events Platform verification code",
        message=f"Your OTP is: {code}\n\nIt expires in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=True,
    )
