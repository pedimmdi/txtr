"""
Shared pytest fixtures for the txtr test suite.

Fixtures defined here are available to every test under core/
without importing them manually.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Profile

User = get_user_model()


@pytest.fixture
def api_client():
    """Unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """
    Primary test user with an attached profile.

    `db` marks that this fixture needs database access.
    """
    account = User.objects.create_user(
        email="alice@example.com",
        password="TestPass123!",
    )
    # Signal or save may already create a profile; ensure username exists.
    profile, _ = Profile.objects.get_or_create(user=account)
    if not profile.username:
        profile.username = "alice"
        profile.save(update_fields=["username"])
    return account


@pytest.fixture
def other_user(db):
    """Second user for follow/DM/permission scenarios."""
    account = User.objects.create_user(
        email="bob@example.com",
        password="TestPass123!",
    )
    profile, _ = Profile.objects.get_or_create(user=account)
    if not profile.username:
        profile.username = "bob"
        profile.save(update_fields=["username"])
    return account


@pytest.fixture
def auth_client(api_client, user):
    """
    API client authenticated as `user` via force_authenticate.

    Skips login endpoints; attaches the user directly to the request.
    Ideal for testing authorized API behavior.
    """
    api_client.force_authenticate(user=user)
    return api_client
