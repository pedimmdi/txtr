"""API tests for hashtag list and hashtag posts."""

import pytest
from hashtags.models import Hashtag
from posts.models import Post


@pytest.mark.django_db
def test_hashtag_list_includes_tag(api_client, user):
    tag = Hashtag.objects.create(name="pytest")
    post = Post.objects.create(author=user, content="hello #pytest")
    post.hashtags.add(tag)

    response = api_client.get("/api/v1/hashtags/")
    assert response.status_code == 200
    results = response.json()["results"]
    names = [t["name"] for t in results]
    assert "pytest" in names


@pytest.mark.django_db
def test_hashtag_posts(api_client, user):
    tag = Hashtag.objects.create(name="txtr")
    post = Post.objects.create(author=user, content="Tagged post")
    post.hashtags.add(tag)

    response = api_client.get("/api/v1/hashtags/txtr/posts/")
    assert response.status_code == 200
    contents = [p["content"] for p in response.json()["results"]]
    assert "Tagged post" in contents
