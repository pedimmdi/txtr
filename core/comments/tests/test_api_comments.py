"""API tests for comments, replies, and comment likes."""

import pytest
from posts.models import Post
from comments.models import Comment, CommentLike


@pytest.fixture
def post(user, db):
    return Post.objects.create(author=user, content="Post for comments")


@pytest.mark.django_db
def test_create_comment(auth_client, user, post):
    url = f"/api/v1/posts/{post.id}/comments/"
    response = auth_client.post(url, {"content": "Nice post"}, format="json")

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Nice post"
    assert data["author"]["username"] == user.profile.username
    assert Comment.objects.filter(post=post, content="Nice post").exists()


@pytest.mark.django_db
def test_list_comments(auth_client, user, post):
    Comment.objects.create(author=user, post=post, content="First")
    response = auth_client.get(f"/api/v1/posts/{post.id}/comments/")

    assert response.status_code == 200
    results = response.json()["results"]
    assert any(c["content"] == "First" for c in results)


@pytest.mark.django_db
def test_reply_to_comment(auth_client, user, post):
    parent = Comment.objects.create(author=user, post=post, content="Parent")
    url = f"/api/v1/posts/{post.id}/comments/{parent.id}/replies/"

    response = auth_client.post(url, {"content": "A reply"}, format="json")

    assert response.status_code == 201
    assert response.json()["content"] == "A reply"
    assert Comment.objects.filter(parent=parent, content="A reply").exists()


@pytest.mark.django_db
def test_comment_like_toggle(auth_client, user, post):
    comment = Comment.objects.create(author=user, post=post, content="Like me")
    url = f"/api/v1/posts/{post.id}/comments/{comment.id}/like/"

    r1 = auth_client.post(url)
    assert r1.status_code == 201
    assert r1.json()["is_liked"] is True
    assert CommentLike.objects.filter(user=user, comment=comment).exists()

    r2 = auth_client.post(url)
    assert r2.status_code == 200
    assert r2.json()["is_liked"] is False
