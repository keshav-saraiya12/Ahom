from django.urls import path
from . import views

urlpatterns = [
    path("google/", views.google_login, name="google-login"),
    path("github/", views.github_login, name="github-login"),
    path("token/refresh/", views.token_refresh, name="token-refresh"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
