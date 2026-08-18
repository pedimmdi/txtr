"""
Smoke tests — verify the test runner and Django setup work.
These do not exercise product features yet.
"""


def test_pytest_is_running():
    """Sanity check: pytest collects and executes this function."""
    assert 1 + 1 == 2


def test_django_settings_loaded():
    """Ensure pytest-django loaded the project settings module."""
    from django.conf import settings

    assert settings.configured
    assert "accounts" in settings.INSTALLED_APPS
    assert "posts" in settings.INSTALLED_APPS
    assert "direct_messages" in settings.INSTALLED_APPS
