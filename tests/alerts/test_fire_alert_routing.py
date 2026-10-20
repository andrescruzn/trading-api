# -*- coding: utf-8 -*-

# ======================================================================
# tests/alerts/test_fire_alert_routing.py
#
# FireAlertService: Telegram al chat vinculado del dueño de la regla o,
# sin vínculo, al chat del sistema; correo al dueño sin request; el
# despacho nunca lanza.
# ======================================================================

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.services.evaluation import FireAlertService

TELEGRAM_API = "app.modules.alerts.channels.telegram_channel.telegram_api"


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_DEFAULT_CHAT_ID="-100999",
        DESKTOP_NOTIFICATIONS_ENABLED=False,
    )


def _rule(channels: dict) -> AlertRule:
    return AlertRule(
        id=1, name="BTC bajo 80k", rule_type="price", rule_spec={},
        channels=channels, user_id=5,
    )


def _make_service(owner=None, user_repo_error: bool = False, mailer=None, user_email=None):
    event_repo = MagicMock()
    event_repo.create.side_effect = lambda event: event
    user_repo = MagicMock()
    if user_repo_error:
        user_repo.get_by_id.side_effect = RuntimeError("BD caída")
    else:
        user_repo.get_by_id.return_value = owner
    service = FireAlertService(
        event_repo=event_repo,
        settings=_settings(),
        mailer=mailer,
        user_email=user_email,
        user_repo=user_repo,
    )
    return service, event_repo, user_repo


class TestTelegramRouting:

    def test_sends_to_owner_linked_chat(self):
        owner = SimpleNamespace(email="ana@example.com", telegram_chat_id=123456)
        svc, event_repo, user_repo = _make_service(owner=owner)

        with patch(TELEGRAM_API, return_value={"message_id": 1}) as api:
            event = svc.fire(rule=_rule({"telegram": True}), title="BTC/USDT por debajo de 80.000")

        user_repo.get_by_id.assert_called_once_with(5)
        assert api.call_args.args[2]["chat_id"] == 123456
        assert event.delivery_status == "sent"
        event_repo.commit.assert_called_once()

    def test_falls_back_to_default_chat_without_link(self):
        owner = SimpleNamespace(email="ana@example.com", telegram_chat_id=None)
        svc, _, _ = _make_service(owner=owner)

        with patch(TELEGRAM_API, return_value={"message_id": 1}) as api:
            svc.fire(rule=_rule({"telegram": True}), title="Alerta")

        assert api.call_args.args[2]["chat_id"] == "-100999"

    def test_owner_lookup_error_falls_back_and_does_not_raise(self):
        svc, _, _ = _make_service(user_repo_error=True)

        with patch(TELEGRAM_API, return_value={"message_id": 1}) as api:
            event = svc.fire(rule=_rule({"telegram": True}), title="Alerta")

        assert api.call_args.args[2]["chat_id"] == "-100999"
        assert event.delivery_status == "sent"

    def test_failed_send_marks_event_failed(self):
        owner = SimpleNamespace(email="ana@example.com", telegram_chat_id=123456)
        svc, event_repo, _ = _make_service(owner=owner)

        with patch(TELEGRAM_API, return_value=None):
            event = svc.fire(rule=_rule({"telegram": True}), title="Alerta")

        assert event.delivery_status == "failed"
        event_repo.commit.assert_called_once()

    def test_owner_not_loaded_when_only_desktop(self):
        svc, _, user_repo = _make_service(owner=None)

        svc.fire(rule=_rule({"desktop": True}), title="Alerta")

        user_repo.get_by_id.assert_not_called()


class TestEmailRouting:

    def test_without_request_email_goes_to_owner(self):
        owner = SimpleNamespace(email="ana@example.com", telegram_chat_id=None)
        mailer = MagicMock()
        mailer.send_by_template.return_value = SimpleNamespace(success=True, error=None)
        svc, _, _ = _make_service(owner=owner, mailer=mailer)

        event = svc.fire(rule=_rule({"email": True}), title="Alerta")

        assert mailer.send_by_template.call_args.kwargs["to_email"] == "ana@example.com"
        assert event.delivery_status == "sent"

    def test_request_email_takes_precedence(self):
        owner = SimpleNamespace(email="ana@example.com", telegram_chat_id=None)
        mailer = MagicMock()
        mailer.send_by_template.return_value = SimpleNamespace(success=True, error=None)
        svc, _, user_repo = _make_service(owner=owner, mailer=mailer, user_email="yo@example.com")

        svc.fire(rule=_rule({"email": True}), title="Alerta")

        assert mailer.send_by_template.call_args.kwargs["to_email"] == "yo@example.com"
        user_repo.get_by_id.assert_not_called()
