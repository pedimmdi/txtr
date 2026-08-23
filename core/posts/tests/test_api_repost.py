"""API tests for repost and quote-repost."""

import pytest
from posts.models import Post


@pytest.fixture
def original_post(other_user, db):
    """A post by Bob that Alice can repost."""
    return Post.objects.create(author=other_user, content="Repost me")


@pytest.mark.django_db
def test_repost_toggle(auth_client, user, original_post):
    """
    First POST creates a pure repost; second POST undoes it.
    """
    url = f"/api/v1/posts/{original_post.id}/repost/"

    # Repost
    response = auth_client.post(url)
    assert response.status_code == 201
    assert response.json()["is_reposted"] is True
    assert Post.objects.filter(
        author=user,
        original_post=original_post,
        content="",
    ).exists()

    # Undo repost
    response = auth_client.post(url)
    assert response.status_code == 200
    assert response.json()["is_reposted"] is False
    assert not Post.objects.filter(
        author=user,
        original_post=original_post,
    ).exists()


@pytest.mark.django_db
def test_cannot_repost_own_post(auth_client, user):
    """Users cannot repost their own posts."""
    own = Post.objects.create(author=user, content="My post")
    response = auth_client.post(f"/api/v1/posts/{own.id}/repost/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_quote_repost(auth_client, user, original_post):
    """
    Quote repost creates a new post with content + original_post link.
    """
    response = auth_client.post(
        f"/api/v1/posts/{original_post.id}/quote/",
        {"content": "My take on this"},
        format="json",
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "My take on this"
    assert data["original_post"] is not None
    assert data["original_post"]["id"] == original_post.id
    assert Post.objects.filter(
        author=user,
        original_post=original_post,
        content="My take on this",
    ).exists()


@pytest.mark.django_db
def test_quote_requires_content(auth_client, original_post):
    """Quote without content must fail."""
    response = auth_client.post(
        f"/api/v1/posts/{original_post.id}/quote/",
        {"content": "   "},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_repost_requires_authentication(api_client, original_post):
    """Anonymous users cannot repost."""
    response = api_client.post(f"/api/v1/posts/{original_post.id}/repost/")
    assert response.status_code in (401, 403)