# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_update_bot_status_service.py
#
# Tests unitarios del UpdateBotStatusService.
#
# ESTRATEGIA:
# - BotRepository y Session son MagicMock.
# - Se prueba el flujo completo de transición de estado, incluyendo
#   los efectos colaterales (started_at / stopped_at).
#
# NOMENCLATURA:
#   test_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.services.bots.update_bot_status_service import (
    UpdateBotStatusService,
)


# ======================================================================
# Helpers
# ======================================================================

def make_bot(status: str = "stopped") -> Bot:
    return Bot(
        id=1,
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode="paper",
        status=status,
        risk_params={"risk_pct": 0.01},
    )


def make_service(bot: Bot | None = None):
    """Retorna (service, mock_repo, mock_session)."""
    mock_repo = MagicMock()
    mock_session = MagicMock()

    # Por defecto get_by_id devuelve el bot dado
    mock_repo.get_by_id.return_value = bot
    # update devuelve el mismo bot que recibe
    mock_repo.update.side_effect = lambda b: b

    service = UpdateBotStatusService(repo=mock_repo, session=mock_session)
    return service, mock_repo, mock_session


# ======================================================================
# TestBotNotFound
# ======================================================================

class TestBotNotFound:
    def test_returns_bot_not_found_when_bot_missing(self):
        service, _, _ = make_service(bot=None)

        result = service.transition(bot_id=99, new_status="running")

        assert result.success is False
        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404


# ======================================================================
# TestInvalidTransitions
# ======================================================================

class TestInvalidTransitions:
    def test_same_status_returns_invalid_transition(self):
        bot = make_bot(status="stopped")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="stopped")

        assert result.success is False
        assert result.error.code == "BOT_INVALID_TRANSITION"
        assert result.error.http_status == 409

    def test_error_to_running_returns_invalid_transition(self):
        bot = make_bot(status="error")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="running")

        assert result.success is False
        assert result.error.code == "BOT_INVALID_TRANSITION"

    def test_stopped_to_paused_returns_invalid_transition(self):
        bot = make_bot(status="stopped")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="paused")

        assert result.success is False
        assert result.error.code == "BOT_INVALID_TRANSITION"

    def test_unknown_status_returns_invalid_status(self):
        bot = make_bot(status="stopped")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="flying")

        assert result.success is False
        assert result.error.code == "BOT_INVALID_STATUS"
        assert result.error.http_status == 422


# ======================================================================
# TestValidTransitions
# ======================================================================

class TestValidTransitions:
    def test_stopped_to_running_succeeds(self):
        bot = make_bot(status="stopped")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="running")

        assert result.success is True
        assert result.data.status == "running"

    def test_running_to_paused_succeeds(self):
        bot = make_bot(status="running")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="paused")

        assert result.success is True
        assert result.data.status == "paused"

    def test_paused_to_running_succeeds(self):
        bot = make_bot(status="paused")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="running")

        assert result.success is True
        assert result.data.status == "running"

    def test_running_to_stopped_succeeds(self):
        bot = make_bot(status="running")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="stopped")

        assert result.success is True
        assert result.data.status == "stopped"

    def test_error_to_stopped_succeeds(self):
        bot = make_bot(status="error")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="stopped")

        assert result.success is True
        assert result.data.status == "stopped"


# ======================================================================
# TestTimestampSideEffects
# ======================================================================

class TestTimestampSideEffects:
    """
    Verifica que started_at y stopped_at se registran correctamente
    durante las transiciones de estado.
    """

    def test_transition_to_running_sets_started_at(self):
        bot = make_bot(status="stopped")
        assert bot.started_at is None

        service, _, _ = make_service(bot=bot)
        result = service.transition(bot_id=1, new_status="running")

        assert result.success is True
        assert result.data.started_at is not None
        assert result.data.started_at.tzinfo is not None  # es timezone-aware

    def test_transition_to_stopped_sets_stopped_at(self):
        bot = make_bot(status="running")
        assert bot.stopped_at is None

        service, _, _ = make_service(bot=bot)
        result = service.transition(bot_id=1, new_status="stopped")

        assert result.success is True
        assert result.data.stopped_at is not None
        assert result.data.stopped_at.tzinfo is not None

    def test_transition_to_paused_does_not_set_stopped_at(self):
        bot = make_bot(status="running")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="paused")

        assert result.success is True
        assert result.data.stopped_at is None

    def test_transition_to_error_does_not_set_timestamps(self):
        bot = make_bot(status="running")
        service, _, _ = make_service(bot=bot)

        result = service.transition(bot_id=1, new_status="error")

        assert result.success is True
        assert result.data.stopped_at is None

    def test_session_commit_is_called_on_success(self):
        bot = make_bot(status="stopped")
        service, _, mock_session = make_service(bot=bot)

        service.transition(bot_id=1, new_status="running")

        mock_session.commit.assert_called_once()

    def test_session_commit_not_called_on_failure(self):
        service, _, mock_session = make_service(bot=None)

        service.transition(bot_id=99, new_status="running")

        mock_session.commit.assert_not_called()
