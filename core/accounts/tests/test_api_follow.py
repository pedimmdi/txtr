"""
API tests for follow / unfollow toggle.
"""

import pytest
from accounts.models import Follow


@pytest.mark.django_db
def test_follow_toggle(auth_client, user, other_user):
    """
    Alice (auth_client/user) follows Bob, then unfollows him.
    """
    url = f"/api/v1/accounts/users/{other_user.profile.username}/follow/"

    # Follow
    response = auth_client.post(url)
    assert response.status_code == 201
    assert response.json()["is_following"] is True
    assert Follow.objects.filter(follower=user, following=other_user).exists()

    # Unfollow
    response = auth_client.post(url)
    assert response.status_code == 200
    assert response.json()["is_following"] is False
    assert not Follow.objects.filter(follower=user, following=other_user).exists()


@pytest.mark.django_db
def test_cannot_follow_self(auth_client, user):
    """Following your own account must be rejected."""
    url = f"/api/v1/accounts/users/{user.profile.username}/follow/"

    response = auth_client.post(url)

    assert response.status_code == 400
    assert not Follow.objects.filter(follower=user, following=user).exists()


@pytest.mark.django_db
def test_follow_requires_authentication(api_client, other_user):
    """Anonymous clients cannot follow anyone."""
    url = f"/api/v1/accounts/users/{other_user.profile.username}/follow/"
    response = api_client.post(url)
    assert response.status_code in (401, 403)
