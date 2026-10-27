# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_execution_mode_rules.py
#
# Reglas del modo de ejecución de un agente (check_execution_mode),
# compartidas por crear y editar: modo válido, minutos para aprobar
# (1–1440), `auto` permitido también en agentes reales (sin variable de
# entorno que lo apague) y timeframe mínimo para señales automáticas.
# ======================================================================

from __future__ import annotations

import pytest

from app.common.config import settings
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.rest.bots.error_messages import BOT_ERROR_MESSAGES
from app.modules.bots.services.bots.execution_mode_rules import check_execution_mode

MIN_SECONDS = 900  # 15m


@pytest.fixture(autouse=True)
def _settings(monkeypatch):
    monkeypatch.setattr(settings, "SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS", MIN_SECONDS)


def _bot(execution_mode="manual", mode="paper", approval_ttl_minutes=None) -> Bot:
    return Bot(
        id=1, name="Agente", strategy_id=1, symbol_id=1, timeframe_id=1, account_id=1,
        feature_set_id=1, mode=mode, status="stopped", risk_params={"risk_pct": 0.01},
        execution_mode=execution_mode, approval_ttl_minutes=approval_ttl_minutes,
    )


def _assert_failed(result, code):
    assert result.success is False
    assert result.error.code == code
    assert result.error.http_status == 422
    assert code in BOT_ERROR_MESSAGES


class TestCheckExecutionMode:

    @pytest.mark.parametrize("execution_mode", ["manual", "approval", "auto"])
    def test_valid_modes_on_paper_with_1h_pass(self, execution_mode):
        assert check_execution_mode(_bot(execution_mode), 3600).success is True

    @pytest.mark.parametrize("execution_mode", ["automatic", "", None])
    def test_unknown_mode_is_rejected(self, execution_mode):
        _assert_failed(check_execution_mode(_bot(execution_mode), 3600), "BOT_INVALID_EXECUTION_MODE")

    @pytest.mark.parametrize("ttl", [0, -5, 1441])
    def test_approval_ttl_out_of_range_is_rejected(self, ttl):
        _assert_failed(check_execution_mode(_bot("approval", approval_ttl_minutes=ttl), 3600), "BOT_INVALID_APPROVAL_TTL")

    @pytest.mark.parametrize("ttl", [1, 60, 1440, None])
    def test_approval_ttl_limits_are_inclusive(self, ttl):
        assert check_execution_mode(_bot("approval", approval_ttl_minutes=ttl), 3600).success is True

    @pytest.mark.parametrize("execution_mode", ["manual", "approval", "auto"])
    def test_real_agents_accept_every_execution_mode(self, execution_mode):
        assert check_execution_mode(_bot(execution_mode, mode="live"), 3600).success is True

    @pytest.mark.parametrize("execution_mode", ["approval", "auto"])
    def test_automation_needs_at_least_the_minimum_timeframe(self, execution_mode):
        result = check_execution_mode(_bot(execution_mode), 300)  # 5m < 15m

        _assert_failed(result, "BOT_TIMEFRAME_TOO_SHORT_FOR_AUTOMATION")
        assert result.error.meta == {"min_seconds": MIN_SECONDS}

    def test_exactly_the_minimum_timeframe_is_allowed(self):
        assert check_execution_mode(_bot("auto"), MIN_SECONDS).success is True

    def test_manual_mode_has_no_timeframe_minimum(self):
        assert check_execution_mode(_bot("manual"), 60).success is True

    def test_unknown_timeframe_skips_the_minimum_check(self):
        assert check_execution_mode(_bot("auto"), None).success is True

    def test_real_auto_agent_still_needs_the_minimum_timeframe(self):
        _assert_failed(
            check_execution_mode(_bot("auto", mode="live"), 60),
            "BOT_TIMEFRAME_TOO_SHORT_FOR_AUTOMATION",
        )
