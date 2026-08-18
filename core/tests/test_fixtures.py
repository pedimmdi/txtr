"""
Verify shared fixtures create usable users and clients.
"""

import pytest
from accounts.models import Profile


@pytest.mark.django_db
def test_user_fixture_has_profile(user):
    """Primary user must exist in DB with a usable profile username."""
    assert user.email == "alice@example.com"
    assert Profile.objects.filter(user=user).exists()
    assert user.profile.username == "alice"


@pytest.mark.django_db
def test_other_user_is_distinct(user, other_user):
    """Two fixtures must yield two different accounts."""
    assert user.id != other_user.id
    assert other_user.profile.username == "bob"


@pytest.mark.django_db
def test_auth_client_is_authenticated(auth_client, user):
    """
    force_authenticate should attach the user so request.user is set.

    Hitting a protected endpoint is deferred to later stages; here we
    only check the client authentication state DRF exposes.
    """
    assert auth_client.handler._force_user == user