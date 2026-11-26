# -*- coding: utf-8 -*-

# ======================================================================
# tests/alerts/test_notifications_service.py
#
# Campana de notificaciones: ListNotificationsService y
# MarkNotificationsSeenService con repositorios MagicMock (sin BD).
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.modules.alerts.domain.alert_event_entity import AlertEvent
from app.modules.alerts.services.notifications import (
    ListNotificationsService,
    MarkNotificationsSeenService,
)
from app.modules.users.domain.user_entity import User

NOW = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)


def _make_user(user_id: int = 1, seen_at: datetime | None = None) -> User:
    return User(id=user_id, email=f"u{user_id}@example.com", role_id=1, notifications_seen_at=seen_at)


def _make_event(event_id: int, ts: datetime, user_id: int = 1) -> AlertEvent:
    # ts naive, como lo devuelve MySQL (UTC sin tzinfo)
    return AlertEvent(
        id=event_id,
        title=f"Alerta {event_id}",
        severity="info",
        payload={},
        user_id=user_id,
        bot_id=7,
        ts=ts.replace(tzinfo=None),
    )


def _make_list_service(user: User | None, events: list[AlertEvent], unread: int = 0):
    event_repo = MagicMock()
    event_repo.list_by_user.side_effect = lambda user_id, limit: [
        e for e in events if e.user_id == user_id
    ][:limit]
    event_repo.count_by_user_after.return_value = unread
    user_repo = MagicMock()
    user_repo.get_by_id.return_value = user
    return ListNotificationsService(event_repo=event_repo, user_repo=user_repo), event_repo


class TestListNotificationsService:

    def test_all_new_when_never_seen(self):
        events = [_make_event(2, NOW), _make_event(1, NOW - timedelta(hours=1))]
        svc, event_repo = _make_list_service(_make_user(seen_at=None), events, unread=2)

        result = svc.list(user_id=1)

        assert result.success is True
        assert result.data.unread_count == 2
        assert [n.is_new for n in result.data.items] == [True, True]
        event_repo.count_by_user_after.assert_called_once_with(user_id=1, after=None)

    def test_only_events_after_seen_at_are_new(self):
        seen_at = NOW - timedelta(minutes=30)
        events = [_make_event(2, NOW), _make_event(1, NOW - timedelta(hours=1))]
        svc, event_repo = _make_list_service(_make_user(seen_at=seen_at), events, unread=1)

        result = svc.list(user_id=1)

        assert result.data.unread_count == 1
        assert [(n.event.id, n.is_new) for n in result.data.items] == [(2, True), (1, False)]
        event_repo.count_by_user_after.assert_called_once_with(user_id=1, after=seen_at)

    def test_passes_limit_and_caps_it(self):
        events = [_make_event(i, NOW - timedelta(minutes=i)) for i in range(1, 80)]
        svc, event_repo = _make_list_service(_make_user(), events)

        small = svc.list(user_id=1, limit=5)
        capped = svc.list(user_id=1, limit=500)

        assert len(small.data.items) == 5
        assert len(capped.data.items) == ListNotificationsService.MAX_LIMIT
        assert event_repo.list_by_user.call_args_list[0].kwargs == {"user_id": 1, "limit": 5}

    def test_only_lists_events_of_the_user(self):
        events = [_make_event(1, NOW, user_id=1), _make_event(2, NOW, user_id=2)]
        svc, event_repo = _make_list_service(_make_user(user_id=2), events)

        result = svc.list(user_id=2)

        assert [n.event.id for n in result.data.items] == [2]
        assert event_repo.list_by_user.call_args.kwargs["user_id"] == 2
        assert event_repo.count_by_user_after.call_args.kwargs["user_id"] == 2

    def test_fails_with_404_when_user_missing(self):
        svc, event_repo = _make_list_service(None, [])

        result = svc.list(user_id=99)

        assert result.success is False
        assert result.error.code == "USER_NOT_FOUND"
        assert result.error.http_status == 404
        event_repo.list_by_user.assert_not_called()


class TestMarkNotificationsSeenService:

    def test_sets_seen_at_and_commits(self):
        user_repo = MagicMock()
        user_repo.set_notifications_seen_at.return_value = True
        svc = MarkNotificationsSeenService(user_repo=user_repo)

        result = svc.mark_seen(user_id=1)

        assert result.success is True
        assert result.data.tzinfo is not None
        user_repo.set_notifications_seen_at.assert_called_once_with(1, result.data)
        user_repo.commit.assert_called_once()

    def test_fails_with_404_and_rolls_back_when_user_missing(self):
        user_repo = MagicMock()
        user_repo.set_notifications_seen_at.return_value = False
        svc = MarkNotificationsSeenService(user_repo=user_repo)

        result = svc.mark_seen(user_id=99)

        assert result.success is False
        assert result.error.code == "USER_NOT_FOUND"
        assert result.error.http_status == 404
        user_repo.commit.assert_not_called()
        user_repo.rollback.assert_called_once()
