# -*- coding: utf-8 -*-

# ======================================================================
# tests/alerts/test_execution_cycle_alerts.py
#
# Paso de alertas del ciclo de ejecución del scheduler: corre con su
# propia sesión (que siempre se cierra) y un fallo no frena a los demás
# pasos. Sin BD: SessionLocal y el provider van mockeados.
# ======================================================================

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.common.contracts import ServiceResult
from app.modules.alerts.services.evaluation import PeriodicAlertsReport
from app.modules.scheduler import execution_cycle

BUILD = "app.modules.alerts.providers.build_periodic_alerts_service"
OTHER_STEPS = (
    "_generate_automatic_signals",
    "_expire_pending_signals",
    "_reconcile_orders",
    "_protect_positions",
    "_poll_telegram",
)


class TestEvaluateAlertRulesStep:

    def test_runs_the_service_with_its_own_session_and_closes_it(self):
        session = MagicMock()
        service = MagicMock()
        service.run.return_value = ServiceResult.ok(PeriodicAlertsReport(checked=2, fired=1))

        with patch.object(execution_cycle, "SessionLocal", return_value=session), \
                patch(BUILD, return_value=service) as build:
            execution_cycle._evaluate_alert_rules()

        build.assert_called_once_with(session)
        service.run.assert_called_once()
        session.close.assert_called_once()

    def test_closes_the_session_even_if_the_service_raises(self):
        session = MagicMock()
        service = MagicMock()
        service.run.side_effect = RuntimeError("BD caída")

        with patch.object(execution_cycle, "SessionLocal", return_value=session), \
                patch(BUILD, return_value=service):
            with pytest.raises(RuntimeError):
                execution_cycle._evaluate_alert_rules()

        session.close.assert_called_once()

    def test_failure_is_isolated_from_the_other_steps(self):
        mocks = {name: MagicMock(__name__=name) for name in OTHER_STEPS}
        failing = MagicMock(side_effect=RuntimeError("alertas caídas"), __name__="_evaluate_alert_rules")

        with patch.multiple(execution_cycle, _evaluate_alert_rules=failing, **mocks):
            execution_cycle.run_execution_cycle()

        failing.assert_called_once()
        for step in mocks.values():
            step.assert_called_once()

    def test_alerts_step_runs_after_protecting_positions(self):
        calls: list[str] = []
        names = (*OTHER_STEPS, "_evaluate_alert_rules")
        mocks = {
            name: MagicMock(side_effect=lambda n=name: calls.append(n), __name__=name)
            for name in names
        }

        with patch.multiple(execution_cycle, **mocks):
            execution_cycle.run_execution_cycle()

        assert calls.index("_evaluate_alert_rules") == calls.index("_protect_positions") + 1
