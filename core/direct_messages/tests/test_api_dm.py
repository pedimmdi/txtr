"""
API tests for direct messages: send, reply, forward, and guards.
"""

import pytest
from posts.models import Post
from direct_messages.models import Conversation, Message


@pytest.mark.django_db
def test_send_message(auth_client, user, other_user):
    """
    Authenticated user can open/create a conversation and send text.
    """
    url = f"/api/v1/dm/{other_user.profile.username}/"

    response = auth_client.post(
        url,
        {"content": "Hey Bob"},
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hey Bob"
    assert data["sender_username"] == user.profile.username

    assert Conversation.objects.filter(participants=user).filter(
        participants=other_user
    ).exists()
    assert Message.objects.filter(
        sender=user,
        content="Hey Bob",
    ).exists()


@pytest.mark.django_db
def test_cannot_message_self(auth_client, user):
    """Messaging yourself must be rejected."""
    url = f"/api/v1/dm/{user.profile.username}/"

    response = auth_client.post(
        url,
        {"content": "Hello me"},
        format="json",
    )

    assert response.status_code == 400
    assert Message.objects.count() == 0


@pytest.mark.django_db
def test_reply_to_message(auth_client, user, other_user):
    """
    POST with reply_to links the new message to a parent in the same conversation.
    """
    url = f"/api/v1/dm/{other_user.profile.username}/"

    parent_res = auth_client.post(
        url,
        {"content": "Parent message"},
        format="json",
    )
    assert parent_res.status_code == 201
    parent_id = parent_res.json()["id"]

    reply_res = auth_client.post(
        url,
        {"content": "This is a reply", "reply_to": parent_id},
        format="json",
    )

    assert reply_res.status_code == 201
    data = reply_res.json()
    assert data["content"] == "This is a reply"
    assert data["reply_to"] is not None
    assert data["reply_to"]["id"] == parent_id
    assert data["reply_to"]["content"] == "Parent message"

    msg = Message.objects.get(id=data["id"])
    assert msg.reply_to_id == parent_id


@pytest.mark.django_db
def test_forward_post_in_dm(auth_client, user, other_user):
    """
    POST with forwarded_post attaches a post card to the message.
    Content may be empty when only forwarding.
    """
    post = Post.objects.create(author=user, content="Post to forward")
    url = f"/api/v1/dm/{other_user.profile.username}/"

    response = auth_client.post(
        url,
        {"forwarded_post": post.id},
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["forwarded_post"] is not None
    assert data["forwarded_post"]["id"] == post.id
    assert "Post to forward" in (data["forwarded_post"].get("content") or "")

    msg = Message.objects.get(id=data["id"])
    assert msg.forwarded_post_id == post.id


@pytest.mark.django_db
def test_list_conversations_includes_new_thread(auth_client, user, other_user):
    """After messaging someone, the conversation appears in GET /api/v1/dm/."""
    auth_client.post(
        f"/api/v1/dm/{other_user.profile.username}/",
        {"content": "Hi"},
        format="json",
    )

    response = auth_client.get("/api/v1/dm/")
    assert response.status_code == 200

    payload = response.json()
    # Endpoint may return a bare list or a paginated object
    items = payload if isinstance(payload, list) else payload.get("results", payload)
    usernames = [
        (item.get("other_user") or {}).get("username")
        for item in items
    ]
    assert other_user.profile.username in usernames


@pytest.mark.django_db
def test_dm_requires_authentication(api_client, other_user):
    """Anonymous users cannot send DMs."""
    response = api_client.post(
        f"/api/v1/dm/{other_user.profile.username}/",
        {"content": "Nope"},
        format="json",
    )
    assert response.status_code in (401, 403)
