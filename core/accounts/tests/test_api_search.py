"""API tests for user search and public profile."""

import pytest


@pytest.mark.django_db
def test_user_search_finds_username(api_client, user):
    """Search by username returns matching public profiles."""
    response = api_client.get("/api/v1/accounts/users/", {"search": "ali"})
    assert response.status_code == 200
    usernames = [p["username"] for p in response.json()["results"]]
    assert user.profile.username in usernames


@pytest.mark.django_db
def test_public_profile_by_username(api_client, user):
    """Anyone can view a public profile by username."""
    response = api_client.get(
        f"/api/v1/accounts/users/{user.profile.username}/"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user.profile.username
    assert "followers_count" in data
    assert "following_count" in data
    assert "is_following" in data


@pytest.mark.django_db
def test_public_profile_not_found(api_client):
    """Unknown username returns 404."""
    response = api_client.get("/api/v1/accounts/users/no_such_user_xyz/")
    assert response.status_code == 404