from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import EmailOTP, RoleChoices, UserProfile

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    OTP_EXPIRY_SECONDS=300,
    OTP_MAX_ATTEMPTS=5,
)
class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    # ---- signup ----

    def test_signup_success(self):
        resp = self.client.post(
            "/auth/signup/",
            {"email": "alice@test.com", "password": "StrongP@ss1", "role": "seeker"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="alice@test.com").exists())
        profile = UserProfile.objects.get(user__email="alice@test.com")
        self.assertEqual(profile.role, RoleChoices.SEEKER)
        self.assertFalse(profile.is_email_verified)

    def test_signup_duplicate_email(self):
        self.client.post(
            "/auth/signup/",
            {"email": "bob@test.com", "password": "StrongP@ss1", "role": "seeker"},
            format="json",
        )
        resp = self.client.post(
            "/auth/signup/",
            {"email": "bob@test.com", "password": "StrongP@ss1", "role": "facilitator"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_no_username_field(self):
        resp = self.client.post(
            "/auth/signup/",
            {
                "email": "nouser@test.com",
                "password": "StrongP@ss1",
                "role": "seeker",
                "username": "sneaky",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="nouser@test.com")
        self.assertEqual(user.username, "nouser@test.com")

    # ---- verify email ----

    def test_verify_email_success(self):
        self.client.post(
            "/auth/signup/",
            {"email": "carol@test.com", "password": "StrongP@ss1", "role": "seeker"},
            format="json",
        )
        otp = EmailOTP.objects.filter(user__email="carol@test.com").first()
        resp = self.client.post(
            "/auth/verify-email/",
            {"email": "carol@test.com", "otp": otp.code},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        profile = UserProfile.objects.get(user__email="carol@test.com")
        self.assertTrue(profile.is_email_verified)

    def test_verify_email_expired(self):
        self.client.post(
            "/auth/signup/",
            {"email": "dave@test.com", "password": "StrongP@ss1", "role": "seeker"},
            format="json",
        )
        otp = EmailOTP.objects.filter(user__email="dave@test.com").first()
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save()
        resp = self.client.post(
            "/auth/verify-email/",
            {"email": "dave@test.com", "otp": otp.code},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", resp.data["detail"].lower())

    def test_verify_email_wrong_otp(self):
        self.client.post(
            "/auth/signup/",
            {"email": "eve@test.com", "password": "StrongP@ss1", "role": "seeker"},
            format="json",
        )
        resp = self.client.post(
            "/auth/verify-email/",
            {"email": "eve@test.com", "otp": "000000"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid", resp.data["detail"].lower())

    # ---- login ----

    def test_login_unverified_blocked(self):
        self.client.post(
            "/auth/signup/",
            {"email": "frank@test.com", "password": "StrongP@ss1", "role": "seeker"},
            format="json",
        )
        resp = self.client.post(
            "/auth/login/",
            {"email": "frank@test.com", "password": "StrongP@ss1"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_verified_success(self):
        self._create_verified_user("grace@test.com", "StrongP@ss1", "seeker")
        resp = self.client.post(
            "/auth/login/",
            {"email": "grace@test.com", "password": "StrongP@ss1"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password(self):
        self._create_verified_user("hank@test.com", "StrongP@ss1", "seeker")
        resp = self.client.post(
            "/auth/login/",
            {"email": "hank@test.com", "password": "wrong"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---- refresh ----

    def test_refresh_token(self):
        self._create_verified_user("ivy@test.com", "StrongP@ss1", "seeker")
        login = self.client.post(
            "/auth/login/",
            {"email": "ivy@test.com", "password": "StrongP@ss1"},
            format="json",
        )
        resp = self.client.post(
            "/auth/refresh/",
            {"refresh": login.data["refresh"]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    # ---- helpers ----

    def _create_verified_user(self, email, password, role):
        user = User.objects.create_user(username=email, email=email, password=password)
        UserProfile.objects.create(user=user, role=role, is_email_verified=True)
        return user
