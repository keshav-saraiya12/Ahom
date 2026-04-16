import requests as http_requests
from django.conf import settings
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import User
from .serializers import UserSerializer, ProfileUpdateSerializer


def _get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["username"] = user.username
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def _find_or_create_user(provider, uid, email, defaults):
    try:
        user = User.objects.get(oauth_provider=provider, oauth_uid=uid)
    except User.DoesNotExist:
        if email:
            try:
                user = User.objects.get(email=email)
                user.oauth_provider = provider
                user.oauth_uid = uid
                user.save(update_fields=["oauth_provider", "oauth_uid"])
                return user
            except User.DoesNotExist:
                pass

        username = defaults.pop("username", email.split("@")[0] if email else f"{provider}_{uid}")
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}_{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            oauth_provider=provider,
            oauth_uid=uid,
            **defaults,
        )
    return user


# ── Google OAuth ──────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@ratelimit(key="ip", rate="20/m", block=True)
def google_login(request):
    """Exchange a Google authorization code for JWT tokens."""
    code = request.data.get("code")
    redirect_uri = request.data.get("redirect_uri", "")
    if not code:
        return Response({"error": "Authorization code required"}, status=400)

    token_resp = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    if token_resp.status_code != 200:
        return Response({"error": "Failed to exchange code with Google"}, status=400)

    id_token = token_resp.json().get("access_token")
    info_resp = http_requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {id_token}"},
        timeout=10,
    )
    if info_resp.status_code != 200:
        return Response({"error": "Failed to fetch Google user info"}, status=400)

    info = info_resp.json()
    user = _find_or_create_user(
        provider="google",
        uid=info["id"],
        email=info.get("email", ""),
        defaults={
            "first_name": info.get("given_name", ""),
            "last_name": info.get("family_name", ""),
            "avatar": info.get("picture", ""),
        },
    )
    tokens = _get_tokens_for_user(user)
    return Response({**tokens, "user": UserSerializer(user).data})


# ── GitHub OAuth ──────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@ratelimit(key="ip", rate="20/m", block=True)
def github_login(request):
    """Exchange a GitHub authorization code for JWT tokens."""
    code = request.data.get("code")
    if not code:
        return Response({"error": "Authorization code required"}, status=400)

    token_resp = http_requests.post(
        "https://github.com/login/oauth/access_token",
        json={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )
    if token_resp.status_code != 200:
        return Response({"error": "Failed to exchange code with GitHub"}, status=400)

    access_token = token_resp.json().get("access_token")
    if not access_token:
        return Response({"error": "GitHub did not return an access token"}, status=400)

    user_resp = http_requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    info = user_resp.json()

    email_resp = http_requests.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    emails = email_resp.json() if email_resp.status_code == 200 else []
    primary_email = next((e["email"] for e in emails if e.get("primary")), info.get("email", ""))

    user = _find_or_create_user(
        provider="github",
        uid=str(info["id"]),
        email=primary_email or "",
        defaults={
            "username": info.get("login", ""),
            "first_name": (info.get("name") or "").split(" ")[0],
            "last_name": " ".join((info.get("name") or "").split(" ")[1:]),
            "avatar": info.get("avatar_url", ""),
        },
    )
    tokens = _get_tokens_for_user(user)
    return Response({**tokens, "user": UserSerializer(user).data})


# ── Token refresh ────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def token_refresh(request):
    """Refresh JWT access token."""
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({"error": "Refresh token required"}, status=400)
    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })
    except Exception:
        return Response({"error": "Invalid or expired refresh token"}, status=401)


# ── Profile ──────────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @method_decorator(ratelimit(key="user", rate="30/m", block=True))
    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)
