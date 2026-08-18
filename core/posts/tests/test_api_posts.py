"""
API tests for post list/create/detail endpoints.
"""

import pytest
from posts.models import Post


@pytest.mark.django_db
def test_create_post_authenticated(auth_client, user):
    """
    Logged-in user can create a post.

    Arrange: authenticated client (fixture)
    Act:     POST /api/v1/posts/ with content
    Assert:  201 + content + author username
    """
    response = auth_client.post(
        "/api/v1/posts/",
        {"content": "Hello from pytest"},
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello from pytest"
    assert data["author"]["username"] == user.profile.username
    assert Post.objects.filter(content="Hello from pytest", author=user).exists()


@pytest.mark.django_db
def test_create_post_requires_authentication(api_client):
    """Anonymous clients must not be allowed to create posts."""
    response = api_client.post(
        "/api/v1/posts/",
        {"content": "Should fail"},
        format="json",
    )

    assert response.status_code in (401, 403)
    assert Post.objects.count() == 0


@pytest.mark.django_db
def test_list_posts_returns_created_post(auth_client, user):
    """
    Public list endpoint includes posts that exist in the database.

    Response is paginated: { count, next, previous, results: [...] }
    """
    Post.objects.create(author=user, content="Listed post")

    response = auth_client.get("/api/v1/posts/")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    contents = [item["content"] for item in data["results"]]
    assert "Listed post" in contents


@pytest.mark.django_db
def test_post_detail(auth_client, user):
    """Retrieve a single post by primary key."""
    post = Post.objects.create(author=user, content="Detail post")

    response = auth_client.get(f"/api/v1/posts/{post.id}/")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post.id
    assert data["content"] == "Detail post"
