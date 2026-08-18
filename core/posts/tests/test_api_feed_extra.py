"""Extra post API tests: feed, bookmarks list, repost, delete."""

import pytest
from posts.models import Post, Bookmark
from accounts.models import Follow


@pytest.mark.django_db
def test_feed_includes_following_posts(auth_client, user, other_user):
    Follow.objects.create(follower=user, following=other_user)
    Post.objects.create(author=other_user, content="From Bob")
    Post.objects.create(author=user, content="From Alice")

    response = auth_client.get("/api/v1/posts/feed/")
    assert response.status_code == 200
    contents = [p["content"] for p in response.json()["results"]]
    assert "From Bob" in contents
    assert "From Alice" in contents


@pytest.mark.django_db
def test_feed_requires_auth(api_client):
    assert api_client.get("/api/v1/posts/feed/").status_code in (401, 403)


@pytest.mark.django_db
def test_bookmark_list(auth_client, user, other_user):
    post = Post.objects.create(author=other_user, content="Saved")
    Bookmark.objects.create(user=user, post=post)

    response = auth_client.get("/api/v1/posts/bookmarks/")
    assert response.status_code == 200
    contents = [p["content"] for p in response.json()["results"]]
    assert "Saved" in contents


@pytest.mark.django_db
def test_repost_toggle(auth_client, user, other_user):
    post = Post.objects.create(author=other_user, content="Repost me")
    url = f"/api/v1/posts/{post.id}/repost/"

    r1 = auth_client.post(url)
    assert r1.status_code == 201
    assert r1.json()["is_reposted"] is True
    assert Post.objects.filter(author=user, original_post=post).exists()

    r2 = auth_client.post(url)
    assert r2.status_code == 200
    assert r2.json()["is_reposted"] is False


@pytest.mark.django_db
def test_cannot_repost_own_post(auth_client, user):
    post = Post.objects.create(author=user, content="Mine")
    response = auth_client.post(f"/api/v1/posts/{post.id}/repost/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_delete_own_post(auth_client, user):
    post = Post.objects.create(author=user, content="Delete me")
    response = auth_client.delete(f"/api/v1/posts/{post.id}/")
    assert response.status_code == 204
    assert not Post.objects.filter(id=post.id).exists()


@pytest.mark.django_db
def test_cannot_delete_others_post(auth_client, other_user):
    post = Post.objects.create(author=other_user, content="Not yours")
    response = auth_client.delete(f"/api/v1/posts/{post.id}/")
    assert response.status_code in (403, 404)
    assert Post.objects.filter(id=post.id).exists()
