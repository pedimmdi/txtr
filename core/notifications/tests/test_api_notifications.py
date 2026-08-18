"""API tests for notifications list, unread count, and mark-read."""

import pytest
from notifications.models import Notification


@pytest.fixture
def notification(user, other_user, db):
    return Notification.objects.create(
        recipient=user,
        sender=other_user,
        notification_type=Notification.NotificationType.FOLLOW,
        is_read=False,
    )


@pytest.mark.django_db
def test_list_notifications(auth_client, notification):
    response = auth_client.get("/api/v1/notifications/")
    assert response.status_code == 200
    results = response.json()["results"]
    assert any(n["id"] == notification.id for n in results)


@pytest.mark.django_db
def test_unread_count(auth_client, notification):
    response = auth_client.get("/api/v1/notifications/unread-count/")
    assert response.status_code == 200
    assert response.json()["unread_count"] >= 1


@pytest.mark.django_db
def test_mark_one_read(auth_client, notification):
    response = auth_client.post(f"/api/v1/notifications/{notification.id}/read/")
    assert response.status_code == 200
    assert response.json()["is_read"] is True
    notification.refresh_from_db()
    assert notification.is_read is True


@pytest.mark.django_db
def test_mark_all_read(auth_client, user, other_user):
    Notification.objects.create(
        recipient=user,
        sender=other_user,
        notification_type=Notification.NotificationType.LIKE,
        is_read=False,
    )
    response = auth_client.post("/api/v1/notifications/read-all/")
    assert response.status_code == 200
    assert Notification.objects.filter(recipient=user, is_read=False).count() == 0


@pytest.mark.django_db
def test_notifications_require_auth(api_client):
    assert api_client.get("/api/v1/notifications/").status_code in (401, 403)
