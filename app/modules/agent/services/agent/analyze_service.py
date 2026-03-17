# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/services/agent/analyze_service.py
#
# PROPÓSITO:
# - Implementar el Prompt Maestro del agente de trading.
#
# FLUJO (4 fases):
#   1. Filtro de Régimen (Python determinístico)
#      → Si el régimen del mercado no coincide con lo que requiere
#        la estrategia, se rechaza ANTES de llamar al LLM.
#
#   2. Validación de Reglas (Python determinístico)
#      → Cada regla de la estrategia se evalúa contra los indicadores
#        reales del último candle. Si UNA falla → rechazado.
#
#   3. Análisis LLM
#      → El LLM recibe el contexto completo (régimen, indicadores,
#        estrategia) y devuelve entry / SL / TP / reasoning en JSON.
#
#   4. Filtro R/R (Python determinístico)
#      → reward / risk >= AGENT_MIN_RR_RATIO (default 2.0).
#        Si no se cumple → rechazado.
#
# CÁLCULO DE POSICIÓN (Python, no el LLM):
#   position_size = (capital × risk_pct) / |entry − stop_loss|
#   risk_pct viene de strategy.parameters.risk_pct (default 0.01 = 1%)
#
# POR QUÉ PYTHON HACE LA MATEMÁTICA (no el LLM):
#   Los LLMs pueden alucinar al calcular. La fórmula es simple y
#   determinística, por lo que es más seguro y confiable en Python.
# ======================================================================

from __future__ import annotations

import json
import logging
from typing import Any

from app.common.contracts import ServiceResult
from app.modules.agent.domain.analysis_result import AnalysisResult, RuleCheckDetail
from app.modules.agent.llm.llm_client import LLMCallError, LLMClient, LLMParseError

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Prompt Maestro por defecto (usado si AGENT_MASTER_PROMPT está vacío)
# ------------------------------------------------------------------
_DEFAULT_SYSTEM_PROMPT = """You are an expert trading analyst. Your role is to analyze market conditions and generate precise trade signals based on technical indicators and a defined strategy.

Given the current market data and strategy context, you must:
1. Analyze each technical indicator provided
2. Determine the optimal entry price, stop loss, and take profit levels
3. Provide a final decision: APPROVED or REJECTED

Rules for REJECTION:
- If market structure does not support the trade
- If there are conflicting or ambiguous signals
- If the risk/reward math does not make sense given current price action

You MUST respond ONLY with valid JSON. No markdown, no explanation outside the JSON:
{
  "decision": "APPROVED" or "REJECTED",
  "entry": <float or null>,
  "stop_loss": <float or null>,
  "take_profit": <float or null>,
  "reasoning": "<one concise sentence>",
  "confidence": <float between 0.0 and 1.0>
}"""

# Operadores soportados en las reglas de la estrategia
_OPERATORS: dict[str, Any] = {
    "lt":  lambda a, b: a < b,
    "gt":  lambda a, b: a > b,
    "lte": lambda a, b: a <= b,
    "gte": lambda a, b: a >= b,
    "eq":  lambda a, b: abs(a - b) < 0.0001,
}


class AnalyzeService:
    """
    Servicio principal del agente de trading (Prompt Maestro).

    Recibe las IDs de símbolo, timeframe, estrategia, cuenta y feature_set.
    Carga todos los datos necesarios, aplica los 4 filtros y retorna
    un AnalysisResult con la decisión completa.

    Dependencias externas (borrowing de otros módulos):
    - StrategyRepository    : cargar la estrategia con sus reglas
    - AccountRepository     : cargar la cuenta (mode, base_currency)
    - AccountBalanceRepository: capital disponible (free balance)
    - CandleFeatureRepository: indicadores técnicos del último candle
    - CandleRepository      : precio actual (close del último candle)
    - SymbolRepository      : nombre del símbolo para el prompt
    - TimeframeRepository   : nombre del timeframe para el prompt
    - LLMClient             : provider de inteligencia artificial
    """

    def __init__(
        self,
        strategy_repo,
        account_repo,
        balance_repo,
        candle_feature_repo,
        candle_repo,
        symbol_repo,
        timeframe_repo,
        llm_client: LLMClient,
        min_rr_ratio: float,
        master_prompt: str,
    ):
        self._strategy_repo = strategy_repo
        self._account_repo = account_repo
        self._balance_repo = balance_repo
        self._candle_feature_repo = candle_feature_repo
        self._candle_repo = candle_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._llm = llm_client
        self._min_rr_ratio = min_rr_ratio
        self._system_prompt = master_prompt or _DEFAULT_SYSTEM_PROMPT

    # ==================================================================
    # Punto de entrada público
    # ==================================================================

    def analyze(
        self,
        symbol_id: int,
        timeframe_id: int,
        strategy_id: int,
        account_id: int,
        feature_set_id: int,
    ) -> ServiceResult[AnalysisResult]:
        """
        Ejecuta el Prompt Maestro completo.

        Returns:
            ServiceResult[AnalysisResult] con la decisión final y todos
            los detalles intermedios de cada fase.
        """

        # ----------------------------------------------------------
        # Paso 0: Cargar datos desde repositorios
        # ----------------------------------------------------------
        strategy = self._strategy_repo.get_by_id(strategy_id)
        if strategy is None:
            return ServiceResult.fail(
                code="AGENT_STRATEGY_NOT_FOUND", http_status=404
            )

        account = self._account_repo.get_by_id(account_id)
        if account is None:
            return ServiceResult.fail(
                code="AGENT_ACCOUNT_NOT_FOUND", http_status=404
            )

        symbol = self._symbol_repo.get_by_id(symbol_id)
        if symbol is None:
            return ServiceResult.fail(
                code="AGENT_SYMBOL_NOT_FOUND", http_status=404
            )

        timeframe = self._timeframe_repo.get_by_id(timeframe_id)
        if timeframe is None:
            return ServiceResult.fail(
                code="AGENT_TIMEFRAME_NOT_FOUND", http_status=404
            )

        # Último candle → precio actual
        candles = self._candle_repo.list_candles(
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            limit=1,
        )
        if not candles:
            return ServiceResult.fail(
                code="AGENT_NO_CANDLE_DATA", http_status=422
            )
        current_price = float(candles[0].close)

        # Features técnicos del último candle
        features_list = self._candle_feature_repo.list_features(
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            feature_set_id=feature_set_id,
            limit=1,
        )
        if not features_list:
            return ServiceResult.fail(
                code="AGENT_NO_FEATURES", http_status=422
            )
        features: dict = features_list[0].features

        # Capital disponible en la moneda base de la cuenta
        base_currency = account.base_currency
        balance = self._balance_repo.get_latest_by_asset(
            account_id=account_id,
            asset=base_currency,
        )
        if balance is None or float(balance.free) <= 0:
            return ServiceResult.fail(
                code="AGENT_NO_BALANCE", http_status=422
            )
        capital = float(balance.free)

        # ----------------------------------------------------------
        # Fase 1: Filtro de Régimen (Python determinístico)
        # ----------------------------------------------------------
        regime = features.get("regime", "unknown")
        regime_check_passed = self._check_regime(
            required_regime=strategy.regime_required,
            current_regime=regime,
        )

        if not regime_check_passed:
            return ServiceResult.ok(
                data=AnalysisResult(
                    decision="REJECTED",
                    rejection_reason="REGIME_MISMATCH",
                    entry=None,
                    stop_loss=None,
                    take_profit=None,
                    position_size=None,
                    rr_ratio=None,
                    reasoning=(
                        f"Régimen actual '{regime}' no coincide con "
                        f"'{strategy.regime_required}' requerido por la estrategia."
                    ),
                    confidence=None,
                    regime_check_passed=False,
                    rules_check_passed=False,
                    rr_check_passed=False,
                    meta=self._build_meta(
                        symbol=symbol, timeframe=timeframe, strategy=strategy,
                        account=account, capital=capital, current_price=current_price,
                        features=features, regime=regime,
                    ),
                )
            )

        # ----------------------------------------------------------
        # Fase 2: Validación de Reglas (Python determinístico)
        # ----------------------------------------------------------
        rules_detail = self._evaluate_rules(
            rules=strategy.rules,
            features=features,
        )
        rules_check_passed = all(r.passed for r in rules_detail)

        if not rules_check_passed:
            failed = [r.indicator for r in rules_detail if not r.passed]
            return ServiceResult.ok(
                data=AnalysisResult(
                    decision="REJECTED",
                    rejection_reason="RULES_NOT_MET",
                    entry=None,
                    stop_loss=None,
                    take_profit=None,
                    position_size=None,
                    rr_ratio=None,
                    reasoning=f"Reglas no cumplidas: {', '.join(failed)}.",
                    confidence=None,
                    regime_check_passed=True,
                    rules_check_passed=False,
                    rr_check_passed=False,
                    rules_detail=rules_detail,
                    meta=self._build_meta(
                        symbol=symbol, timeframe=timeframe, strategy=strategy,
                        account=account, capital=capital, current_price=current_price,
                        features=features, regime=regime,
                    ),
                )
            )

        # ----------------------------------------------------------
        # Fase 3: Análisis LLM
        # ----------------------------------------------------------
        user_message = self._build_user_message(
            symbol=symbol,
            timeframe=timeframe,
            strategy=strategy,
            current_price=current_price,
            capital=capital,
            base_currency=base_currency,
            regime=regime,
            features=features,
            rules_detail=rules_detail,
        )

        try:
            raw_response = self._llm.complete(
                system_prompt=self._system_prompt,
                user_message=user_message,
            )
        except LLMCallError as exc:
            logger.error("LLM call failed: %s", exc)
            return ServiceResult.fail(
                code="AGENT_LLM_CALL_FAILED",
                http_status=502,
                meta={"detail": str(exc)},
            )

        try:
            llm_data = self._parse_llm_response(raw_response)
        except LLMParseError as exc:
            logger.error("LLM parse error: %s", exc)
            return ServiceResult.fail(
                code="AGENT_LLM_PARSE_ERROR",
                http_status=502,
                meta={"raw": raw_response[:500]},
            )

        # Si el LLM mismo rechazó la operación
        if llm_data.get("decision") != "APPROVED":
            return ServiceResult.ok(
                data=AnalysisResult(
                    decision="REJECTED",
                    rejection_reason="LLM_REJECTED",
                    entry=llm_data.get("entry"),
                    stop_loss=llm_data.get("stop_loss"),
                    take_profit=llm_data.get("take_profit"),
                    position_size=None,
                    rr_ratio=None,
                    reasoning=llm_data.get("reasoning", ""),
                    confidence=llm_data.get("confidence"),
                    regime_check_passed=True,
                    rules_check_passed=True,
                    rr_check_passed=False,
                    rules_detail=rules_detail,
                    meta=self._build_meta(
                        symbol=symbol, timeframe=timeframe, strategy=strategy,
                        account=account, capital=capital, current_price=current_price,
                        features=features, regime=regime,
                    ),
                )
            )

        # Extraer precios sugeridos por el LLM
        try:
            entry = float(llm_data["entry"])
            stop_loss = float(llm_data["stop_loss"])
            take_profit = float(llm_data["take_profit"])
        except (KeyError, TypeError, ValueError):
            return ServiceResult.fail(
                code="AGENT_LLM_MISSING_PRICES",
                http_status=502,
                meta={"raw": str(llm_data)},
            )

        # ----------------------------------------------------------
        # Cálculo de posición (Python, no el LLM)
        # position_size = (capital × risk_pct) / |entry − stop_loss|
        # ----------------------------------------------------------
        risk_pct = float(strategy.parameters.get("risk_pct", 0.01))
        price_risk = abs(entry - stop_loss)

        if price_risk < 1e-10:
            return ServiceResult.fail(
                code="AGENT_INVALID_PRICE_RISK", http_status=422
            )

        position_size = (capital * risk_pct) / price_risk

        # ----------------------------------------------------------
        # Fase 4: Filtro R/R (Python determinístico)
        # reward / risk >= min_rr_ratio
        # ----------------------------------------------------------
        reward = abs(take_profit - entry)
        rr_ratio = reward / price_risk
        rr_check_passed = rr_ratio >= self._min_rr_ratio

        if not rr_check_passed:
            return ServiceResult.ok(
                data=AnalysisResult(
                    decision="REJECTED",
                    rejection_reason="RR_RATIO_TOO_LOW",
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=round(position_size, 8),
                    rr_ratio=round(rr_ratio, 4),
                    reasoning=(
                        f"R/R ratio {rr_ratio:.2f} es menor al mínimo "
                        f"requerido de {self._min_rr_ratio:.1f}."
                    ),
                    confidence=llm_data.get("confidence"),
                    regime_check_passed=True,
                    rules_check_passed=True,
                    rr_check_passed=False,
                    rules_detail=rules_detail,
                    meta=self._build_meta(
                        symbol=symbol, timeframe=timeframe, strategy=strategy,
                        account=account, capital=capital, current_price=current_price,
                        features=features, regime=regime,
                    ),
                )
            )

        # ----------------------------------------------------------
        # ¡Operación APROBADA! — pasó los 4 filtros
        # ----------------------------------------------------------
        return ServiceResult.ok(
            data=AnalysisResult(
                decision="APPROVED",
                rejection_reason=None,
                entry=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=round(position_size, 8),
                rr_ratio=round(rr_ratio, 4),
                reasoning=llm_data.get("reasoning", ""),
                confidence=llm_data.get("confidence"),
                regime_check_passed=True,
                rules_check_passed=True,
                rr_check_passed=True,
                rules_detail=rules_detail,
                meta=self._build_meta(
                    symbol=symbol, timeframe=timeframe, strategy=strategy,
                    account=account, capital=capital, current_price=current_price,
                    features=features, regime=regime,
                ),
            )
        )

    # ==================================================================
    # Helpers privados
    # ==================================================================

    @staticmethod
    def _check_regime(required_regime: str | None, current_regime: str) -> bool:
        """
        Fase 1: Verifica que el régimen del mercado sea el esperado.
        Si regime_required es None, la estrategia funciona en cualquier régimen.
        """
        if required_regime is None:
            return True
        return current_regime == required_regime

    @staticmethod
    def _evaluate_rules(rules: list[dict], features: dict) -> list[RuleCheckDetail]:
        """
        Fase 2: Evalúa cada regla de la estrategia contra los features actuales.

        Formato de regla:
            {"indicator": "rsi_14", "operator": "lt", "value": 30}

        El campo "value" puede ser:
        - Un número: comparar directamente (rsi_14 < 30)
        - Un string de otro indicator: comparar contra ese valor (ema_20 > ema_50)
        """
        details: list[RuleCheckDetail] = []

        for rule in rules:
            indicator = rule.get("indicator", "")
            operator = rule.get("operator", "")
            threshold = rule.get("value")

            actual = features.get(indicator)

            # El threshold puede ser el nombre de otro indicator
            if isinstance(threshold, str) and threshold in features:
                compare = features[threshold]
            else:
                try:
                    compare = float(threshold)
                except (TypeError, ValueError):
                    compare = None

            # Evaluar la regla con el operador correspondiente
            if actual is None or compare is None or operator not in _OPERATORS:
                passed = False
            else:
                try:
                    passed = _OPERATORS[operator](float(actual), float(compare))
                except Exception:
                    passed = False

            details.append(
                RuleCheckDetail(
                    indicator=indicator,
                    operator=operator,
                    threshold=threshold,
                    actual_value=actual,
                    passed=passed,
                )
            )

        return details

    @staticmethod
    def _parse_llm_response(raw: str) -> dict:
        """
        Parsea la respuesta JSON del LLM.

        Limpia bloques de markdown (```json ... ```) antes de parsear.

        Raises:
            LLMParseError: si el JSON es inválido o faltan campos requeridos.
        """
        cleaned = raw.strip()

        # Remover bloques de código markdown si los hay
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Quitar la primera línea (```json o ```) y la última (```)
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMParseError(raw_response=raw, detail=str(exc)) from exc

        # Validar campo mínimo requerido
        if "decision" not in data:
            raise LLMParseError(
                raw_response=raw,
                detail="Campo 'decision' faltante en respuesta del LLM.",
            )

        return data

    @staticmethod
    def _build_user_message(
        symbol,
        timeframe,
        strategy,
        current_price: float,
        capital: float,
        base_currency: str,
        regime: str,
        features: dict,
        rules_detail: list[RuleCheckDetail],
    ) -> str:
        """Construye el mensaje de usuario para el LLM con todo el contexto de mercado."""

        def _fmt(val, decimals: int = 2) -> str:
            if val is None:
                return "N/A"
            try:
                return f"{float(val):.{decimals}f}"
            except (TypeError, ValueError):
                return str(val)

        # Representar las reglas como texto legible
        rules_text = "\n".join(
            f"  - {r.indicator} {r.operator} {r.threshold}"
            f" [actual={_fmt(r.actual_value, 4)}] → {'✓ PASS' if r.passed else '✗ FAIL'}"
            for r in rules_detail
        )

        return (
            f"=== TRADING ANALYSIS REQUEST ===\n\n"
            f"SYMBOL: {symbol.symbol}\n"
            f"TIMEFRAME: {timeframe.code}\n"
            f"CURRENT PRICE: {_fmt(current_price, 8)}\n\n"
            f"STRATEGY: {strategy.name} v{strategy.version}\n"
            f"TYPE: {strategy.parameters.get('strategy_type', 'N/A')}\n"
            f"REQUIRED REGIME: {strategy.regime_required or 'any'}\n"
            f"CURRENT REGIME: {regime}\n\n"
            f"=== TECHNICAL INDICATORS (latest candle) ===\n"
            f"RSI(14):   {_fmt(features.get('rsi_14'), 2)}\n"
            f"EMA(20):   {_fmt(features.get('ema_20'), 4)}\n"
            f"EMA(50):   {_fmt(features.get('ema_50'), 4)}\n"
            f"EMA(200):  {_fmt(features.get('ema_200'), 4)}\n"
            f"MACD:      {_fmt(features.get('macd'), 4)} | "
            f"Signal: {_fmt(features.get('macd_signal'), 4)} | "
            f"Hist: {_fmt(features.get('macd_hist'), 4)}\n"
            f"ATR(14):   {_fmt(features.get('atr_14'), 4)}\n"
            f"BB Upper:  {_fmt(features.get('bb_upper'), 4)} | "
            f"Mid: {_fmt(features.get('bb_mid'), 4)} | "
            f"Lower: {_fmt(features.get('bb_lower'), 4)}\n"
            f"Vol Rel:   {_fmt(features.get('vol_rel'), 2)}x\n\n"
            f"=== STRATEGY RULES (all passed) ===\n"
            f"{rules_text or '  (no rules defined)'}\n\n"
            f"=== ACCOUNT ===\n"
            f"Capital:    {_fmt(capital, 2)} {base_currency}\n"
            f"Risk/Trade: {float(strategy.parameters.get('risk_pct', 0.01)) * 100:.1f}%\n\n"
            f"Based on the above, provide entry, stop_loss, and take_profit levels.\n"
            f"Ensure your suggested levels make mathematical sense for this "
            f"symbol's current price range."
        )

    @staticmethod
    def _build_meta(
        symbol, timeframe, strategy, account, capital, current_price, features, regime
    ) -> dict:
        """Snapshot del contexto para persistir en raw_output / auditoría."""
        return {
            "symbol": symbol.symbol,
            "timeframe": timeframe.code,
            "strategy": strategy.name,
            "strategy_version": strategy.version,
            "account_mode": account.mode,
            "capital": capital,
            "base_currency": account.base_currency,
            "current_price": current_price,
            "regime": regime,
            "features_snapshot": {
                k: features.get(k)
                for k in (
                    "rsi_14", "ema_20", "ema_50", "ema_200",
                    "macd", "atr_14", "vol_rel", "regime",
                )
            },
        }
