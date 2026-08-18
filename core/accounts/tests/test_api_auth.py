"""
API tests for registration and JWT login.
"""

import pytest
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


@pytest.mark.django_db
def test_register_user(api_client):
    """
    Guest can register with email + password.
    A profile should be created by the post_save signal.
    """
    response = api_client.post(
        "/api/v1/accounts/register/",
        {
            "email": "newbie@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newbie@example.com"
    assert "password" not in data  # write_only

    user = User.objects.get(email="newbie@example.com")
    assert user.check_password("StrongPass123!")
    assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_register_rejects_duplicate_email(api_client, user):
    """Registering with an existing email must fail validation."""
    response = api_client.post(
        "/api/v1/accounts/register/",
        {
            "email": user.email,
            "password": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_login_returns_jwt_tokens(api_client, user):
    """
    Login with email/password returns access + refresh tokens.

    SimpleJWT uses USERNAME_FIELD as the credential key → 'email'.
    """
    response = api_client.post(
        "/api/v1/accounts/login/",
        {
            "email": user.email,
            "password": "TestPass123!",
        },
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert "access" in data
    assert "refresh" in data
    assert data.get("user", {}).get("email") == user.email


@pytest.mark.django_db
def test_login_rejects_bad_password(api_client, user):
    """Wrong password must not issue tokens."""
    response = api_client.post(
        "/api/v1/accounts/login/",
        {
            "email": user.email,
            "password": "WrongPassword999!",
        },
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_access_token_can_call_protected_endpoint(api_client, user):
    """
    After login, Bearer access token authorizes API requests
    without force_authenticate.
    """
    login = api_client.post(
        "/api/v1/accounts/login/",
        {"email": user.email, "password": "TestPass123!"},
        format="json",
    )
    assert login.status_code == 200
    access = login.json()["access"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = api_client.get("/api/v1/accounts/profile/")
    assert response.status_code == 200
    assert response.json()["username"] == user.profile.username
