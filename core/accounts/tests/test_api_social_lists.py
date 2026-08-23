"""API tests for followers/following lists and profile update."""

import pytest
from accounts.models import Follow


@pytest.mark.django_db
def test_followers_list(api_client, user, other_user):
    """
    When Bob follows Alice, Alice's followers list includes Bob.
    """
    Follow.objects.create(follower=other_user, following=user)

    response = api_client.get(
        f"/api/v1/accounts/users/{user.profile.username}/followers/"
    )
    assert response.status_code == 200
    usernames = [p["username"] for p in response.json()["results"]]
    assert other_user.profile.username in usernames


@pytest.mark.django_db
def test_following_list(api_client, user, other_user):
    """
    When Alice follows Bob, Alice's following list includes Bob.
    """
    Follow.objects.create(follower=user, following=other_user)

    response = api_client.get(
        f"/api/v1/accounts/users/{user.profile.username}/following/"
    )
    assert response.status_code == 200
    usernames = [p["username"] for p in response.json()["results"]]
    assert other_user.profile.username in usernames


@pytest.mark.django_db
def test_update_own_profile(auth_client, user):
    """Authenticated user can update bio (and other profile fields)."""
    response = auth_client.put(
        "/api/v1/accounts/profile/",
        {"bio": "Hello from tests"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "Hello from tests"
    user.profile.refresh_from_db()
    assert user.profile.bio == "Hello from tests"