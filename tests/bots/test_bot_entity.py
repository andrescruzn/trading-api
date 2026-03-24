# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_bot_entity.py
#
# Tests unitarios de la entidad de dominio Bot.
#
# ESTRATEGIA:
# - Sin mocks ni I/O. Solo Python puro.
# - Se prueba la máquina de estados (can_transition_to) y los
#   accessors de risk_params.
#
# NOMENCLATURA:
#   test_<método>_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

import pytest

from app.modules.bots.domain.bot_entity import Bot


# ======================================================================
# Helpers
# ======================================================================

def make_bot(status: str = "stopped", risk_params: dict | None = None) -> Bot:
    return Bot(
        id=1,
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=2,
        feature_set_id=1,
        mode="paper",
        status=status,
        risk_params=risk_params if risk_params is not None else {"risk_pct": 0.02},
    )


# ======================================================================
# TestBotStateMachine — can_transition_to
# ======================================================================

class TestBotStateMachine:
    """
    Verifica todas las transiciones válidas e inválidas definidas en
    Bot._ALLOWED_TRANSITIONS.
    """

    # --- Transiciones VÁLIDAS ---

    def test_stopped_can_transition_to_running(self):
        bot = make_bot(status="stopped")
        assert bot.can_transition_to("running") is True

    def test_running_can_transition_to_paused(self):
        bot = make_bot(status="running")
        assert bot.can_transition_to("paused") is True

    def test_running_can_transition_to_stopped(self):
        bot = make_bot(status="running")
        assert bot.can_transition_to("stopped") is True

    def test_running_can_transition_to_error(self):
        bot = make_bot(status="running")
        assert bot.can_transition_to("error") is True

    def test_paused_can_transition_to_running(self):
        bot = make_bot(status="paused")
        assert bot.can_transition_to("running") is True

    def test_paused_can_transition_to_stopped(self):
        bot = make_bot(status="paused")
        assert bot.can_transition_to("stopped") is True

    def test_error_can_transition_to_stopped(self):
        bot = make_bot(status="error")
        assert bot.can_transition_to("stopped") is True

    # --- Transiciones INVÁLIDAS ---

    def test_stopped_cannot_transition_to_same_status(self):
        bot = make_bot(status="stopped")
        assert bot.can_transition_to("stopped") is False

    def test_stopped_cannot_transition_to_paused(self):
        # No se puede pausar un bot detenido
        bot = make_bot(status="stopped")
        assert bot.can_transition_to("paused") is False

    def test_stopped_cannot_transition_to_error(self):
        bot = make_bot(status="stopped")
        assert bot.can_transition_to("error") is False

    def test_error_cannot_transition_to_running(self):
        # Desde error hay que pasar por stopped primero
        bot = make_bot(status="error")
        assert bot.can_transition_to("running") is False

    def test_error_cannot_transition_to_paused(self):
        bot = make_bot(status="error")
        assert bot.can_transition_to("paused") is False

    def test_running_cannot_transition_to_same_status(self):
        bot = make_bot(status="running")
        assert bot.can_transition_to("running") is False

    def test_paused_cannot_transition_to_error(self):
        bot = make_bot(status="paused")
        assert bot.can_transition_to("error") is False


# ======================================================================
# TestBotIsActive
# ======================================================================

class TestBotIsActive:
    """is_active() debe retornar True solo para running y paused."""

    def test_running_is_active(self):
        assert make_bot(status="running").is_active() is True

    def test_paused_is_active(self):
        assert make_bot(status="paused").is_active() is True

    def test_stopped_is_not_active(self):
        assert make_bot(status="stopped").is_active() is False

    def test_error_is_not_active(self):
        assert make_bot(status="error").is_active() is False


# ======================================================================
# TestBotRiskParams
# ======================================================================

class TestBotRiskParams:
    """Accessors sobre risk_params deben leer correctamente del dict."""

    def test_risk_pct_reads_from_risk_params(self):
        bot = make_bot(risk_params={"risk_pct": 0.015})
        assert bot.risk_pct == 0.015

    def test_risk_pct_defaults_to_001_when_missing(self):
        bot = make_bot(risk_params={})
        assert bot.risk_pct == 0.01

    def test_max_drawdown_pct_reads_from_risk_params(self):
        bot = make_bot(risk_params={"risk_pct": 0.01, "max_drawdown_pct": 0.20})
        assert bot.max_drawdown_pct == 0.20

    def test_max_drawdown_pct_is_none_when_not_set(self):
        bot = make_bot(risk_params={"risk_pct": 0.01})
        assert bot.max_drawdown_pct is None
