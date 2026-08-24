"""API tests for comment update/delete permissions."""

import pytest
from posts.models import Post
from comments.models import Comment


@pytest.fixture
def post(user, db):
    return Post.objects.create(author=user, content="Post for comment perms")


@pytest.fixture
def comment(user, post, db):
    return Comment.objects.create(
        author=user, post=post, content="Original comment"
    )


@pytest.mark.django_db
def test_author_can_update_comment(auth_client, post, comment):
    response = auth_client.patch(
        f"/api/v1/posts/{post.id}/comments/{comment.id}/",
        {"content": "Edited comment"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Edited comment"
    comment.refresh_from_db()
    assert comment.content == "Edited comment"


@pytest.mark.django_db
def test_non_author_cannot_update_comment(api_client, other_user, post, comment):
    api_client.force_authenticate(user=other_user)
    response = api_client.patch(
        f"/api/v1/posts/{post.id}/comments/{comment.id}/",
        {"content": "Hacked"},
        format="json",
    )
    assert response.status_code in (403, 404)
    comment.refresh_from_db()
    assert comment.content == "Original comment"


@pytest.mark.django_db
def test_author_can_delete_comment(auth_client, post, comment):
    response = auth_client.delete(
        f"/api/v1/posts/{post.id}/comments/{comment.id}/"
    )
    assert response.status_code == 204
    assert not Comment.objects.filter(id=comment.id).exists()


@pytest.mark.django_db
def test_non_author_cannot_delete_comment(api_client, other_user, post, comment):
    api_client.force_authenticate(user=other_user)
    response = api_client.delete(
        f"/api/v1/posts/{post.id}/comments/{comment.id}/"
    )
    assert response.status_code in (403, 404)
    assert Comment.objects.filter(id=comment.id).exists()