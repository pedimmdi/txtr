"""API tests for public profile and own profile update."""

import pytest


@pytest.mark.django_db
def test_public_profile(api_client, other_user):
    response = api_client.get(
        f"/api/v1/accounts/users/{other_user.profile.username}/"
    )
    assert response.status_code == 200
    assert response.json()["username"] == other_user.profile.username


@pytest.mark.django_db
def test_my_profile(auth_client, user):
    response = auth_client.get("/api/v1/accounts/profile/")
    assert response.status_code == 200
    assert response.json()["username"] == user.profile.username


@pytest.mark.django_db
def test_update_my_profile(auth_client, user):
    response = auth_client.put(
        "/api/v1/accounts/profile/",
        {"bio": "Updated bio from tests"},
        format="json",
    )
    assert response.status_code == 200
    user.profile.refresh_from_db()
    assert user.profile.bio == "Updated bio from tests"
