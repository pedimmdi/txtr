"""API tests for post update/delete permissions and bookmark list."""

import pytest
from posts.models import Post, Bookmark


@pytest.fixture
def post(user, db):
    return Post.objects.create(author=user, content="Original content")


@pytest.mark.django_db
def test_author_can_update_post(auth_client, post):
    """Author can PATCH their own post."""
    response = auth_client.patch(
        f"/api/v1/posts/{post.id}/",
        {"content": "Updated content"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated content"
    post.refresh_from_db()
    assert post.content == "Updated content"


@pytest.mark.django_db
def test_non_author_cannot_update_post(api_client, other_user, post):
    """Another user must not be able to edit someone else's post."""
    api_client.force_authenticate(user=other_user)
    response = api_client.patch(
        f"/api/v1/posts/{post.id}/",
        {"content": "Hacked"},
        format="json",
    )
    assert response.status_code in (403, 404)
    post.refresh_from_db()
    assert post.content == "Original content"


@pytest.mark.django_db
def test_author_can_delete_post(auth_client, post):
    """Author can DELETE their own post."""
    response = auth_client.delete(f"/api/v1/posts/{post.id}/")
    assert response.status_code == 204
    assert not Post.objects.filter(id=post.id).exists()


@pytest.mark.django_db
def test_non_author_cannot_delete_post(api_client, other_user, post):
    """Another user must not be able to delete someone else's post."""
    api_client.force_authenticate(user=other_user)
    response = api_client.delete(f"/api/v1/posts/{post.id}/")
    assert response.status_code in (403, 404)
    assert Post.objects.filter(id=post.id).exists()


@pytest.mark.django_db
def test_bookmark_list(auth_client, user, post):
    """Bookmarked posts appear in GET /api/v1/posts/bookmarks/."""
    Bookmark.objects.create(user=user, post=post)

    response = auth_client.get("/api/v1/posts/bookmarks/")
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()["results"]]
    assert post.id in ids


@pytest.mark.django_db
def test_bookmark_list_requires_auth(api_client):
    """Anonymous clients cannot list bookmarks."""
    response = api_client.get("/api/v1/posts/bookmarks/")
    assert response.status_code in (401, 403)