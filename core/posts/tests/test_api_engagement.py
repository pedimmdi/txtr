"""
API tests for like and bookmark toggles.
"""

import pytest
from posts.models import Post, Like, Bookmark


@pytest.fixture
def post(user, db):
    """A post authored by the primary user."""
    return Post.objects.create(author=user, content="Engagement target")


@pytest.mark.django_db
def test_like_toggle(auth_client, user, post):
    """
    First POST likes the post; second POST unlikes it.
    """
    url = f"/api/v1/posts/{post.id}/like/"

    # Like
    response = auth_client.post(url)
    assert response.status_code == 201
    assert response.json()["is_liked"] is True
    assert Like.objects.filter(user=user, post=post).exists()

    # Unlike
    response = auth_client.post(url)
    assert response.status_code == 200
    assert response.json()["is_liked"] is False
    assert not Like.objects.filter(user=user, post=post).exists()


@pytest.mark.django_db
def test_like_requires_authentication(api_client, post):
    """Anonymous users cannot like posts."""
    response = api_client.post(f"/api/v1/posts/{post.id}/like/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_bookmark_toggle(auth_client, user, post):
    """First POST bookmarks; second POST removes the bookmark."""
    url = f"/api/v1/posts/{post.id}/bookmark/"

    response = auth_client.post(url)
    assert response.status_code == 201
    assert response.json()["is_bookmarked"] is True
    assert Bookmark.objects.filter(user=user, post=post).exists()

    response = auth_client.post(url)
    assert response.status_code == 200
    assert response.json()["is_bookmarked"] is False
    assert not Bookmark.objects.filter(user=user, post=post).exists()
