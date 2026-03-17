# -*- coding: utf-8 -*-

# ======================================================================
# tests/agent/test_analyze_service.py
#
# Tests unitarios del AnalyzeService (Prompt Maestro).
#
# ESTRATEGIA:
# - Todos los repositorios y el LLMClient son mocks (MagicMock).
# - El LLM devuelve JSON pre-definido — no hay llamadas reales a la API.
# - Se prueban las 4 fases de forma independiente.
#
# NOMENCLATURA:
#   test_<fase>_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

import json
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.modules.agent.services.agent.analyze_service import AnalyzeService


# ======================================================================
# Helpers / Factories
# ======================================================================

def make_strategy(
    id: int = 1,
    name: str = "BTC Trend Follow",
    version: str = "1.0.0",
    strategy_type: str = "trend_following",
    regime_required: str | None = "trend_up",
    risk_pct: float = 0.01,
    rules: list | None = None,
):
    """Crea una entidad Strategy mockeada."""
    s = MagicMock()
    s.id = id
    s.name = name
    s.version = version
    s.regime_required = regime_required
    s.rules = rules or [
        {"indicator": "rsi_14", "operator": "lt", "value": 40},
        {"indicator": "ema_20", "operator": "gt", "value": "ema_50"},
    ]
    s.parameters = {
        "strategy_type": strategy_type,
        "regime_required": regime_required,
        "risk_pct": risk_pct,
    }
    return s


def make_account(id: int = 1, base_currency: str = "USDT", mode: str = "paper"):
    a = MagicMock()
    a.id = id
    a.base_currency = base_currency
    a.mode = mode
    return a


def make_symbol(id: int = 1, symbol: str = "BTC/USDT"):
    s = MagicMock()
    s.id = id
    s.symbol = symbol
    return s


def make_timeframe(id: int = 1, code: str = "1h"):
    t = MagicMock()
    t.id = id
    t.code = code
    return t


def make_candle(close: float = 42000.0):
    c = MagicMock()
    c.close = Decimal(str(close))
    return c


def make_features(
    regime: str = "trend_up",
    rsi_14: float = 35.0,
    ema_20: float = 41500.0,
    ema_50: float = 41000.0,
    ema_200: float = 40000.0,
    macd: float = 120.0,
    macd_signal: float = 90.0,
    macd_hist: float = 30.0,
    atr_14: float = 850.0,
    bb_upper: float = 43000.0,
    bb_mid: float = 42000.0,
    bb_lower: float = 41000.0,
    vol_rel: float = 1.5,
):
    """Crea una entidad CandleFeature mockeada con features predeterminados."""
    f = MagicMock()
    f.features = {
        "regime":     regime,
        "rsi_14":     rsi_14,
        "ema_20":     ema_20,
        "ema_50":     ema_50,
        "ema_200":    ema_200,
        "macd":       macd,
        "macd_signal":macd_signal,
        "macd_hist":  macd_hist,
        "atr_14":     atr_14,
        "bb_upper":   bb_upper,
        "bb_mid":     bb_mid,
        "bb_lower":   bb_lower,
        "vol_rel":    vol_rel,
    }
    return f


def make_balance(free: float = 10000.0):
    b = MagicMock()
    b.free = Decimal(str(free))
    return b


def make_llm_response(
    decision: str = "APPROVED",
    entry: float = 42000.0,
    stop_loss: float = 41000.0,
    take_profit: float = 44000.0,
    reasoning: str = "Strong uptrend with good indicators.",
    confidence: float = 0.82,
) -> str:
    """Crea una respuesta JSON mockeada del LLM."""
    return json.dumps({
        "decision":   decision,
        "entry":      entry,
        "stop_loss":  stop_loss,
        "take_profit":take_profit,
        "reasoning":  reasoning,
        "confidence": confidence,
    })


def make_service(
    strategy=None,
    account=None,
    balance=None,
    candles=None,
    features=None,
    symbol=None,
    timeframe=None,
    llm_response: str | None = None,
    min_rr_ratio: float = 2.0,
) -> AnalyzeService:
    """
    Crea un AnalyzeService con todas las dependencias mockeadas.
    Los repositorios devuelven los objetos provistos (o None si no se pasan).
    """
    strategy_repo = MagicMock()
    strategy_repo.get_by_id.return_value = strategy or make_strategy()

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account or make_account()

    balance_repo = MagicMock()
    balance_repo.get_latest_by_asset.return_value = balance or make_balance()

    candle_repo = MagicMock()
    candle_repo.list_candles.return_value = candles if candles is not None else [make_candle()]

    candle_feature_repo = MagicMock()
    candle_feature_repo.list_features.return_value = (
        features if features is not None else [make_features()]
    )

    symbol_repo = MagicMock()
    symbol_repo.get_by_id.return_value = symbol or make_symbol()

    timeframe_repo = MagicMock()
    timeframe_repo.get_by_id.return_value = timeframe or make_timeframe()

    llm_client = MagicMock()
    llm_client.complete.return_value = (
        llm_response if llm_response is not None else make_llm_response()
    )

    return AnalyzeService(
        strategy_repo=strategy_repo,
        account_repo=account_repo,
        balance_repo=balance_repo,
        candle_feature_repo=candle_feature_repo,
        candle_repo=candle_repo,
        symbol_repo=symbol_repo,
        timeframe_repo=timeframe_repo,
        llm_client=llm_client,
        min_rr_ratio=min_rr_ratio,
        master_prompt="",
    )


# ======================================================================
# Tests — Carga de datos
# ======================================================================

class TestAnalyzeDataLoading:

    def test_fails_when_strategy_not_found(self):
        svc = make_service()
        svc._strategy_repo.get_by_id.return_value = None

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=99, account_id=1, feature_set_id=1
        )

        assert result.success is False
        assert result.error.code == "AGENT_STRATEGY_NOT_FOUND"
        assert result.error.http_status == 404

    def test_fails_when_account_not_found(self):
        svc = make_service()
        svc._account_repo.get_by_id.return_value = None

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=99, feature_set_id=1
        )

        assert result.success is False
        assert result.error.code == "AGENT_ACCOUNT_NOT_FOUND"

    def test_fails_when_no_candles(self):
        svc = make_service(candles=[])

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.success is False
        assert result.error.code == "AGENT_NO_CANDLE_DATA"

    def test_fails_when_no_features(self):
        svc = make_service(features=[])

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.success is False
        assert result.error.code == "AGENT_NO_FEATURES"

    def test_fails_when_no_balance(self):
        svc = make_service()
        svc._balance_repo.get_latest_by_asset.return_value = None

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.success is False
        assert result.error.code == "AGENT_NO_BALANCE"

    def test_fails_when_balance_is_zero(self):
        svc = make_service(balance=make_balance(free=0.0))

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.success is False
        assert result.error.code == "AGENT_NO_BALANCE"


# ======================================================================
# Tests — Fase 1: Filtro de Régimen
# ======================================================================

class TestRegimeFilter:

    def test_rejected_when_regime_does_not_match(self):
        """
        La estrategia requiere trend_up, pero el mercado está sideways.
        Debe rechazar ANTES de llamar al LLM.
        """
        strategy = make_strategy(regime_required="trend_up")
        features = [make_features(regime="sideways")]
        svc = make_service(strategy=strategy, features=features)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.success is True
        assert result.data.decision == "REJECTED"
        assert result.data.rejection_reason == "REGIME_MISMATCH"
        assert result.data.regime_check_passed is False
        # El LLM NO debe ser llamado
        svc._llm.complete.assert_not_called()

    def test_approved_when_regime_matches(self):
        """Régimen coincide — el análisis continúa a la siguiente fase."""
        strategy = make_strategy(regime_required="trend_up")
        features = [make_features(regime="trend_up")]
        svc = make_service(strategy=strategy, features=features)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.regime_check_passed is True

    def test_passes_when_regime_required_is_none(self):
        """
        Si regime_required es None, la estrategia acepta cualquier régimen.
        """
        strategy = make_strategy(regime_required=None)
        features = [make_features(regime="sideways")]
        svc = make_service(strategy=strategy, features=features)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.regime_check_passed is True


# ======================================================================
# Tests — Fase 2: Validación de Reglas
# ======================================================================

class TestRulesValidation:

    def test_rejected_when_rule_fails(self):
        """
        Regla: rsi_14 < 40, pero rsi actual = 65. Debe rechazar.
        """
        strategy = make_strategy(
            regime_required="trend_up",
            rules=[{"indicator": "rsi_14", "operator": "lt", "value": 40}],
        )
        features = [make_features(regime="trend_up", rsi_14=65.0)]
        svc = make_service(strategy=strategy, features=features)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.decision == "REJECTED"
        assert result.data.rejection_reason == "RULES_NOT_MET"
        assert result.data.rules_check_passed is False
        # Hay exactamente un detalle y está marcado como fallido
        assert len(result.data.rules_detail) == 1
        assert result.data.rules_detail[0].passed is False
        svc._llm.complete.assert_not_called()

    def test_approved_when_all_rules_pass(self):
        """Todas las reglas se cumplen — el análisis pasa a la fase LLM."""
        strategy = make_strategy(
            regime_required="trend_up",
            rules=[{"indicator": "rsi_14", "operator": "lt", "value": 40}],
        )
        features = [make_features(regime="trend_up", rsi_14=30.0)]
        svc = make_service(strategy=strategy, features=features)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.rules_check_passed is True

    def test_rule_with_indicator_as_value(self):
        """
        Regla: ema_20 > ema_50 (el threshold es otro indicator).
        """
        strategy = make_strategy(
            regime_required="trend_up",
            rules=[{"indicator": "ema_20", "operator": "gt", "value": "ema_50"}],
        )
        # ema_20 = 41500 > ema_50 = 41000 → PASS
        features = [make_features(regime="trend_up", ema_20=41500.0, ema_50=41000.0)]
        svc = make_service(strategy=strategy, features=features)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.rules_check_passed is True
        assert result.data.rules_detail[0].passed is True


# ======================================================================
# Tests — Fase 3: LLM
# ======================================================================

class TestLLMIntegration:

    def test_rejected_when_llm_rejects(self):
        """
        El LLM analiza y decide REJECTED. El servicio respeta esa decisión.
        """
        llm_resp = make_llm_response(
            decision="REJECTED",
            reasoning="Market structure is not favorable.",
        )
        svc = make_service(llm_response=llm_resp)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.decision == "REJECTED"
        assert result.data.rejection_reason == "LLM_REJECTED"
        assert "not favorable" in result.data.reasoning

    def test_fails_when_llm_call_raises(self):
        """
        Si el LLM lanza una excepción (red, auth, timeout), el servicio
        retorna un ServiceResult.fail con código AGENT_LLM_CALL_FAILED.
        """
        from app.modules.agent.llm.llm_client import LLMCallError

        svc = make_service()
        svc._llm.complete.side_effect = LLMCallError("openai", "Connection timeout")

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.success is False
        assert result.error.code == "AGENT_LLM_CALL_FAILED"
        assert result.error.http_status == 502

    def test_fails_when_llm_returns_invalid_json(self):
        """
        Si el LLM devuelve texto que no es JSON válido, el servicio
        retorna AGENT_LLM_PARSE_ERROR.
        """
        svc = make_service(llm_response="I think you should buy BTC right now!")

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.success is False
        assert result.error.code == "AGENT_LLM_PARSE_ERROR"

    def test_llm_response_with_markdown_block_is_parsed(self):
        """
        El LLM a veces devuelve JSON envuelto en ```json ... ```.
        El servicio debe limpiar el bloque antes de parsear.
        """
        llm_resp = (
            "```json\n"
            + make_llm_response()
            + "\n```"
        )
        svc = make_service(llm_response=llm_resp)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        # Si el parsing falló, habría error. Si pasó, tenemos un resultado.
        assert result.success is True or result.error.code != "AGENT_LLM_PARSE_ERROR"


# ======================================================================
# Tests — Fase 4: Filtro R/R
# ======================================================================

class TestRRFilter:

    def test_rejected_when_rr_ratio_too_low(self):
        """
        entry=42000, SL=41500, TP=42600
        risk   = 42000 - 41500 = 500
        reward = 42600 - 42000 = 600
        rr     = 600 / 500 = 1.2  → menor a 2.0 → REJECTED
        """
        llm_resp = make_llm_response(
            entry=42000, stop_loss=41500, take_profit=42600
        )
        svc = make_service(llm_response=llm_resp, min_rr_ratio=2.0)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.decision == "REJECTED"
        assert result.data.rejection_reason == "RR_RATIO_TOO_LOW"
        assert result.data.rr_check_passed is False
        assert result.data.rr_ratio == pytest.approx(1.2, abs=0.01)

    def test_approved_when_rr_ratio_meets_threshold(self):
        """
        entry=42000, SL=41000, TP=44000
        risk   = 1000
        reward = 2000
        rr     = 2.0 → exactamente el mínimo → APPROVED
        """
        llm_resp = make_llm_response(
            entry=42000, stop_loss=41000, take_profit=44000
        )
        svc = make_service(llm_response=llm_resp, min_rr_ratio=2.0)

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.decision == "APPROVED"
        assert result.data.rr_check_passed is True
        assert result.data.rr_ratio == pytest.approx(2.0, abs=0.01)


# ======================================================================
# Tests — Cálculo de posición
# ======================================================================

class TestPositionSizing:

    def test_position_size_calculation(self):
        """
        Capital = 10,000 USDT
        risk_pct = 1% = 0.01
        entry = 42,000 | SL = 41,000
        price_risk = 1,000
        position_size = 10,000 × 0.01 / 1,000 = 0.1 BTC
        """
        strategy = make_strategy(risk_pct=0.01)
        llm_resp = make_llm_response(
            entry=42000, stop_loss=41000, take_profit=44000
        )
        svc = make_service(
            strategy=strategy,
            balance=make_balance(free=10000.0),
            llm_response=llm_resp,
        )

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.data.decision == "APPROVED"
        assert result.data.position_size == pytest.approx(0.1, abs=1e-6)


# ======================================================================
# Tests — Camino feliz completo (APPROVED)
# ======================================================================

class TestFullApprovedPath:

    def test_full_analysis_approved(self):
        """
        Prueba el camino completo desde datos → LLM → resultado APPROVED.
        Verifica que todas las fases estén marcadas como exitosas.
        """
        strategy = make_strategy(
            regime_required="trend_up",
            risk_pct=0.01,
            rules=[{"indicator": "rsi_14", "operator": "lt", "value": 40}],
        )
        features = [make_features(regime="trend_up", rsi_14=32.0)]
        llm_resp = make_llm_response(
            entry=42000, stop_loss=41000, take_profit=44000, confidence=0.85
        )
        svc = make_service(
            strategy=strategy,
            features=features,
            balance=make_balance(free=10000.0),
            llm_response=llm_resp,
        )

        result = svc.analyze(
            symbol_id=1, timeframe_id=1, strategy_id=1, account_id=1, feature_set_id=1
        )

        assert result.success is True
        assert result.data.decision == "APPROVED"
        assert result.data.rejection_reason is None
        assert result.data.regime_check_passed is True
        assert result.data.rules_check_passed is True
        assert result.data.rr_check_passed is True
        assert result.data.entry == pytest.approx(42000.0)
        assert result.data.stop_loss == pytest.approx(41000.0)
        assert result.data.take_profit == pytest.approx(44000.0)
        assert result.data.rr_ratio == pytest.approx(2.0, abs=0.01)
        assert result.data.position_size == pytest.approx(0.1, abs=1e-6)
        assert result.data.confidence == pytest.approx(0.85)
        assert result.data.meta["symbol"] == "BTC/USDT"
        # El LLM fue llamado exactamente una vez
        svc._llm.complete.assert_called_once()
