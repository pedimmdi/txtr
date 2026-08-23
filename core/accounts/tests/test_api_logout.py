"""API tests for logout (refresh token blacklist)."""

import pytest
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api_client, user):
    """
    After logout, the refresh token must be blacklisted and
    cannot be used to obtain a new access token.

    Tokens are created via RefreshToken.for_user to avoid AuthRateThrottle
    when the full suite hits /login/ many times.
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    refresh_str = str(refresh)

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    response = api_client.post(
        "/api/v1/accounts/logout/",
        {"refresh": refresh_str},
        format="json",
    )
    assert response.status_code == 205

    outstanding = OutstandingToken.objects.filter(user=user)
    assert outstanding.exists()
    assert BlacklistedToken.objects.filter(token__in=outstanding).exists()

    # Refresh with blacklisted token must fail
    refresh_response = api_client.post(
        "/api/token/refresh/",
        {"refresh": refresh_str},
        format="json",
    )
    assert refresh_response.status_code == 401


@pytest.mark.django_db
def test_logout_requires_refresh_token(auth_client):
    """Logout without a refresh token must return 400."""
    response = auth_client.post("/api/v1/accounts/logout/", {}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_logout_rejects_invalid_refresh(auth_client):
    """Invalid refresh token must return 400."""
    response = auth_client.post(
        "/api/v1/accounts/logout/",
        {"refresh": "not-a-valid-token"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_logout_requires_authentication(api_client, user):
    """Anonymous clients cannot logout."""
    response = api_client.post(
        "/api/v1/accounts/logout/",
        {"refresh": "whatever"},
        format="json",
    )
    assert response.status_code in (401, 403)