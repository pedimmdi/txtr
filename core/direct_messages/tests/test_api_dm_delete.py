"""API tests for deleting own DM messages."""

import pytest


@pytest.mark.django_db
def test_delete_own_message(auth_client, other_user):
    send = auth_client.post(
        f"/api/v1/dm/{other_user.profile.username}/",
        {"content": "temp"},
        format="json",
    )
    assert send.status_code == 201
    msg_id = send.json()["id"]

    response = auth_client.delete(
        f"/api/v1/dm/{other_user.profile.username}/{msg_id}/"
    )
    assert response.status_code == 204
