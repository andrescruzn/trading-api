# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_generate_signal_service.py
#
# Tests unitarios del GenerateSignalService.
#
# ESTRATEGIA:
# - BotRepository, SignalRepository, Session y AnalyzeService son mocks.
# - El AnalyzeService devuelve AnalysisResult pre-definidos, sin LLM real.
# - Se prueban las validaciones iniciales y el mapeo del resultado
#   del agente a una Signal entity.
#
# FLUJO TESTEADO:
#   1. Bot no encontrado → BOT_NOT_FOUND
#   2. Bot no activo (stopped/error) → BOT_NOT_ACTIVE
#   3. Bot sin feature_set_id → BOT_NO_FEATURE_SET
#   4. Error técnico del agente → propaga el código de error
#   5. Señal APPROVED con entry > stop_loss → action = "buy"
#   6. Señal APPROVED con entry < stop_loss → action = "sell"
#   7. Señal REJECTED → action = "hold", approved = False
#   8. Señal hold (approved, sin precios) → action = "hold"
#
# NOMENCLATURA:
#   test_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.services.signals.generate_signal_service import (
    GenerateSignalService,
)


# ======================================================================
# Helpers / Factories
# ======================================================================

def make_bot(
    status: str = "running",
    feature_set_id: int | None = 1,
) -> Bot:
    return Bot(
        id=1,
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=feature_set_id,
        mode="paper",
        status=status,
        risk_params={"risk_pct": 0.01},
    )


def make_analysis_result(
    approved: bool = True,
    entry: float | None = 50000.0,
    stop_loss: float | None = 49000.0,
    take_profit: float | None = 52000.0,
    position_size: float | None = 0.02,
    rr_ratio: float | None = 2.0,
    confidence: float | None = 0.85,
) -> MagicMock:
    """Crea un AnalysisResult mock con los valores dados."""
    result = MagicMock()
    result.approved = approved
    result.entry = entry
    result.stop_loss = stop_loss
    result.take_profit = take_profit
    result.position_size = position_size
    result.rr_ratio = rr_ratio
    result.confidence = confidence
    result.meta = {"features_snapshot": {"rsi_14": 35.5, "regime": "trend_up"}}
    result.to_dict.return_value = {
        "approved": approved,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "rr_ratio": rr_ratio,
        "confidence": confidence,
    }
    return result


def make_signal(bot_id: int = 1, action: str = "buy") -> Signal:
    return Signal(
        id=10,
        bot_id=bot_id,
        ts=datetime.now(tz=timezone.utc),
        action=action,
        approved=True,
        reasons={"approved": True},
        confidence=Decimal("0.85"),
        entry_price=Decimal("50000"),
        stop_loss=Decimal("49000"),
        take_profit=Decimal("52000"),
        position_size=Decimal("0.02"),
        rr_ratio=Decimal("2.0"),
        features_hash="abc123",
    )


_MISSING = object()  # Sentinel para distinguir "no pasado" de "explícitamente None"


def make_service(
    bot=_MISSING,
    analysis_result=None,
    analysis_ok: bool = True,
    analysis_error_code: str = "AGENT_NO_DATA",
):
    """Retorna (service, mock_bot_repo, mock_signal_repo, mock_analyze, mock_session)."""
    mock_bot_repo = MagicMock()
    mock_signal_repo = MagicMock()
    mock_analyze = MagicMock()
    mock_session = MagicMock()

    # Si no se pasó bot → crear uno running por defecto
    # Si se pasó None explícitamente → simular "no encontrado"
    resolved_bot = make_bot() if bot is _MISSING else bot
    mock_bot_repo.get_by_id.return_value = resolved_bot

    if analysis_ok:
        ar = analysis_result or make_analysis_result()
        mock_analyze.analyze.return_value = ServiceResult.ok(data=ar)
    else:
        mock_analyze.analyze.return_value = ServiceResult.fail(
            code=analysis_error_code, http_status=503
        )

    # create devuelve la signal con id asignado
    def _create_signal(s: Signal) -> Signal:
        s.id = 10
        return s

    mock_signal_repo.create.side_effect = _create_signal

    service = GenerateSignalService(
        bot_repo=mock_bot_repo,
        signal_repo=mock_signal_repo,
        analyze_service=mock_analyze,
        session=mock_session,
    )
    return service, mock_bot_repo, mock_signal_repo, mock_analyze, mock_session


# ======================================================================
# TestBotValidation
# ======================================================================

class TestBotValidation:
    def test_bot_not_found_returns_error(self):
        service, _, _, _, _ = make_service(bot=None)

        result = service.generate(bot_id=99)

        assert result.success is False
        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404

    def test_stopped_bot_returns_not_active_error(self):
        bot = make_bot(status="stopped")
        service, _, _, _, _ = make_service(bot=bot)

        result = service.generate(bot_id=1)

        assert result.success is False
        assert result.error.code == "BOT_NOT_ACTIVE"
        assert result.error.http_status == 409

    def test_error_status_bot_returns_not_active_error(self):
        bot = make_bot(status="error")
        service, _, _, _, _ = make_service(bot=bot)

        result = service.generate(bot_id=1)

        assert result.success is False
        assert result.error.code == "BOT_NOT_ACTIVE"

    def test_paused_bot_can_generate_signals(self):
        # paused IS active per domain logic (is_active() = True)
        bot = make_bot(status="paused")
        service, _, _, mock_analyze, _ = make_service(bot=bot)

        service.generate(bot_id=1)

        mock_analyze.analyze.assert_called_once()

    def test_bot_without_feature_set_returns_error(self):
        bot = make_bot(feature_set_id=None)
        service, _, _, _, _ = make_service(bot=bot)

        result = service.generate(bot_id=1)

        assert result.success is False
        assert result.error.code == "BOT_NO_FEATURE_SET"
        assert result.error.http_status == 422


# ======================================================================
# TestAgentError
# ======================================================================

class TestAgentError:
    def test_agent_technical_error_propagates(self):
        service, _, _, _, _ = make_service(
            analysis_ok=False,
            analysis_error_code="AGENT_NO_DATA",
        )

        result = service.generate(bot_id=1)

        assert result.success is False
        assert result.error.code == "AGENT_NO_DATA"

    def test_signal_not_persisted_on_agent_error(self):
        service, _, mock_signal_repo, _, _ = make_service(
            analysis_ok=False,
            analysis_error_code="AGENT_LLM_ERROR",
        )

        service.generate(bot_id=1)

        mock_signal_repo.create.assert_not_called()


# ======================================================================
# TestApprovedSignalDirection
# ======================================================================

class TestApprovedSignalDirection:
    """
    Cuando el agente aprueba la señal, la dirección (buy/sell) se infiere
    de la relación entry vs stop_loss.
    """

    def test_entry_greater_than_stop_loss_infers_buy(self):
        # entry=50000, SL=49000 → entry > SL → BUY
        ar = make_analysis_result(
            approved=True,
            entry=50000.0,
            stop_loss=49000.0,
        )
        service, _, _, _, _ = make_service(analysis_result=ar)

        result = service.generate(bot_id=1)

        assert result.success is True
        assert result.data.action == "buy"
        assert result.data.approved is True

    def test_entry_less_than_stop_loss_infers_sell(self):
        # entry=49000, SL=50000 → entry < SL → SELL (short)
        ar = make_analysis_result(
            approved=True,
            entry=49000.0,
            stop_loss=50000.0,
        )
        service, _, _, _, _ = make_service(analysis_result=ar)

        result = service.generate(bot_id=1)

        assert result.success is True
        assert result.data.action == "sell"
        assert result.data.approved is True

    def test_approved_signal_without_prices_defaults_to_hold(self):
        # Aprobada pero sin precios → hold
        ar = make_analysis_result(
            approved=True,
            entry=None,
            stop_loss=None,
        )
        service, _, _, _, _ = make_service(analysis_result=ar)

        result = service.generate(bot_id=1)

        assert result.success is True
        assert result.data.action == "hold"


# ======================================================================
# TestRejectedSignal
# ======================================================================

class TestRejectedSignal:
    """
    Las señales rechazadas se persisten como 'hold' con approved=False.
    Esto garantiza trazabilidad completa de todas las señales.
    """

    def test_rejected_signal_has_hold_action(self):
        ar = make_analysis_result(approved=False, entry=None, stop_loss=None)
        service, _, _, _, _ = make_service(analysis_result=ar)

        result = service.generate(bot_id=1)

        assert result.success is True
        assert result.data.action == "hold"

    def test_rejected_signal_has_approved_false(self):
        ar = make_analysis_result(approved=False, entry=None, stop_loss=None)
        service, _, _, _, _ = make_service(analysis_result=ar)

        result = service.generate(bot_id=1)

        assert result.data.approved is False

    def test_rejected_signal_is_persisted(self):
        ar = make_analysis_result(approved=False, entry=None, stop_loss=None)
        service, _, mock_signal_repo, _, _ = make_service(analysis_result=ar)

        service.generate(bot_id=1)

        # Incluso las señales rechazadas se guardan (trazabilidad)
        mock_signal_repo.create.assert_called_once()


# ======================================================================
# TestSignalFields
# ======================================================================

class TestSignalFields:
    """Verifica que los campos de la señal se construyen correctamente."""

    def test_approved_signal_has_price_fields(self):
        ar = make_analysis_result(
            approved=True,
            entry=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            position_size=0.02,
            rr_ratio=2.0,
            confidence=0.85,
        )
        service, _, _, _, _ = make_service(analysis_result=ar)

        result = service.generate(bot_id=1)

        assert result.success is True
        signal = result.data
        assert signal.entry_price == Decimal("50000.0")
        assert signal.stop_loss == Decimal("49000.0")
        assert signal.take_profit == Decimal("52000.0")
        assert signal.position_size == Decimal("0.02")
        assert signal.rr_ratio == Decimal("2.0")
        assert signal.confidence == Decimal("0.85")

    def test_signal_has_features_hash(self):
        service, _, _, _, _ = make_service()

        result = service.generate(bot_id=1)

        assert result.success is True
        assert result.data.features_hash is not None
        assert len(result.data.features_hash) <= 64  # máximo 64 chars

    def test_session_commit_called_on_success(self):
        service, _, _, _, mock_session = make_service()

        service.generate(bot_id=1)

        mock_session.commit.assert_called_once()

    def test_analyze_service_receives_bot_context(self):
        bot = make_bot(status="running", feature_set_id=7)
        service, _, _, mock_analyze, _ = make_service(bot=bot)

        service.generate(bot_id=1)

        mock_analyze.analyze.assert_called_once_with(
            symbol_id=bot.symbol_id,
            timeframe_id=bot.timeframe_id,
            strategy_id=bot.strategy_id,
            account_id=bot.account_id,
            feature_set_id=7,
        )
