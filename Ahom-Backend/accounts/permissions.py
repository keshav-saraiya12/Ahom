from rest_framework.permissions import BasePermission

from .models import RoleChoices


class IsEmailVerified(BasePermission):
    """Deny access to users whose email is not yet verified."""

    message = "Email is not verified."
    code = "email_not_verified"

    def has_permission(self, request, view):
        profile = getattr(request.user, "profile", None)
        return profile is not None and profile.is_email_verified


class IsSeeker(BasePermission):
    message = "Only seekers can perform this action."
    code = "not_seeker"

    def has_permission(self, request, view):
        profile = getattr(request.user, "profile", None)
        return profile is not None and profile.role == RoleChoices.SEEKER


class IsFacilitator(BasePermission):
    message = "Only facilitators can perform this action."
    code = "not_facilitator"

    def has_permission(self, request, view):
        profile = getattr(request.user, "profile", None)
        return profile is not None and profile.role == RoleChoices.FACILITATOR
