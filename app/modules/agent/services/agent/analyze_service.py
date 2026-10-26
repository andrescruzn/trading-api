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
import math
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.common.contracts import ServiceResult
from app.modules.agent.domain.analysis_result import AnalysisResult, RuleCheckDetail
from app.modules.agent.llm.llm_client import LLMCallError, LLMClient, LLMParseError
from app.modules.features.domain.indicator_catalog import missing_for_rules
from app.modules.strategies.domain.rule_evaluation import evaluate_rule

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


# Regla del 1 %: nunca arriesgar más del 1 % del capital por operación
_MAX_RISK_PCT = 0.01


def _effective_risk_pct(value: object) -> float:
    """risk_pct pedido (bot o estrategia) acotado a (0, 1 %]; inválido → 1 %."""
    try:
        pct = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return _MAX_RISK_PCT
    if not math.isfinite(pct) or pct <= 0:
        return _MAX_RISK_PCT
    return min(pct, _MAX_RISK_PCT)


def _positive_price(value: object) -> float | None:
    """Número finito y > 0, o None (el LLM puede devolver texto, null, NaN…)."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _confidence(value: object) -> float | None:
    """Confianza del LLM acotada a [0, 1]; fuera de rango o inválida → None."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and 0.0 <= number <= 1.0 else None


def _reject_json_constant(name: str) -> None:
    """json.loads acepta NaN/Infinity por defecto; aquí se rechazan."""
    raise ValueError(f"Valor no permitido en la respuesta del LLM: {name}")


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
        max_entry_atr_distance: float = 1.0,
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
        self._max_entry_atr_distance = max_entry_atr_distance
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
        owner_id: int | None = None,
        risk_pct: float | None = None,
        as_of: datetime | None = None,
        capital: Decimal | None = None,
    ) -> ServiceResult[AnalysisResult]:
        """
        Ejecuta el Prompt Maestro completo.

        Args:
            owner_id: si viene, la cuenta debe ser de ese usuario (None = admin).
            risk_pct: riesgo por operación del bot; si no viene se usa el de la
                      estrategia. En ambos casos se acota a la Regla del 1 %.
            as_of:    analiza la vela con ese ts (o la anterior) en vez de la
                      última. El scheduler pasa la última vela CERRADA para no
                      decidir con la vela en formación.
            capital:  capital del agente en el fondo común (M11). Si viene, la
                      regla del 1 % usa este monto y no el saldo libre de la
                      cuenta (que es de todos los participantes).

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
        # Una cuenta ajena se trata como inexistente (no revela su saldo)
        if account is None or (owner_id is not None and account.user_id != owner_id):
            return ServiceResult.fail(
                code="AGENT_ACCOUNT_NOT_FOUND", http_status=404
            )

        effective_risk_pct = _effective_risk_pct(
            risk_pct if risk_pct is not None else strategy.parameters.get("risk_pct")
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
            to_ts=as_of,
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
            to_ts=as_of,
            limit=1,
        )
        if not features_list:
            return ServiceResult.fail(
                code="AGENT_NO_FEATURES", http_status=422
            )
        features: dict = features_list[0].features

        # El conjunto de indicadores debe cubrir lo que piden las reglas;
        # si no, cada regla sin dato se rechazaría en silencio.
        missing = missing_for_rules(strategy.rules, set(features))
        if missing:
            return ServiceResult.fail(
                code="AGENT_FEATURE_SET_INCOMPATIBLE",
                http_status=422,
                meta={"missing": sorted(missing)},
            )

        # Capital: el del agente en el fondo común si viene; si no, el saldo
        # libre en la moneda base de la cuenta.
        base_currency = account.base_currency
        if capital is not None:
            if capital <= 0:
                return ServiceResult.fail(code="AGENT_NO_FUND_CAPITAL", http_status=422)
            capital = float(capital)
        else:
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
            risk_pct=effective_risk_pct,
        )

        try:
            completion = self._llm.complete(
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

        raw_response = completion.text
        # Qué servicio/modelo respondió y cuánto tardó: va en cada resultado
        # posterior a la fase 3 (y en el meta de los errores de respuesta).
        llm_call = {
            "llm_provider": completion.provider,
            "llm_model": completion.model,
            "llm_latency_ms": completion.latency_ms,
            "llm_failed_providers": completion.failed_providers,
        }

        try:
            llm_data = self._parse_llm_response(raw_response)
        except LLMParseError as exc:
            logger.error("LLM parse error (%s): %s", completion.provider, exc)
            return ServiceResult.fail(
                code="AGENT_LLM_PARSE_ERROR",
                http_status=502,
                meta={"raw": raw_response[:500], **llm_call},
            )

        # Si el LLM mismo rechazó la operación
        if llm_data.get("decision") != "APPROVED":
            return ServiceResult.ok(
                data=AnalysisResult(
                    decision="REJECTED",
                    rejection_reason="LLM_REJECTED",
                    entry=_positive_price(llm_data.get("entry")),
                    stop_loss=_positive_price(llm_data.get("stop_loss")),
                    take_profit=_positive_price(llm_data.get("take_profit")),
                    position_size=None,
                    rr_ratio=None,
                    reasoning=str(llm_data.get("reasoning", ""))[:1000],
                    confidence=_confidence(llm_data.get("confidence")),
                    regime_check_passed=True,
                    rules_check_passed=True,
                    rr_check_passed=False,
                    rules_detail=rules_detail,
                    meta=self._build_meta(
                        symbol=symbol, timeframe=timeframe, strategy=strategy,
                        account=account, capital=capital, current_price=current_price,
                        features=features, regime=regime,
                    ),
                    **llm_call,
                )
            )

        # Extraer precios sugeridos por el LLM (números finitos y > 0)
        entry = _positive_price(llm_data.get("entry"))
        stop_loss = _positive_price(llm_data.get("stop_loss"))
        take_profit = _positive_price(llm_data.get("take_profit"))
        if entry is None or stop_loss is None or take_profit is None:
            return ServiceResult.fail(
                code="AGENT_LLM_MISSING_PRICES",
                http_status=502,
                meta={"raw": str(llm_data)[:500], **llm_call},
            )

        def _reject(reason: str, reasoning: str) -> ServiceResult[AnalysisResult]:
            return ServiceResult.ok(
                data=AnalysisResult(
                    decision="REJECTED",
                    rejection_reason=reason,
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=None,
                    rr_ratio=None,
                    reasoning=reasoning,
                    confidence=_confidence(llm_data.get("confidence")),
                    regime_check_passed=True,
                    rules_check_passed=True,
                    rr_check_passed=False,
                    rules_detail=rules_detail,
                    meta=self._build_meta(
                        symbol=symbol, timeframe=timeframe, strategy=strategy,
                        account=account, capital=capital, current_price=current_price,
                        features=features, regime=regime,
                    ),
                    **llm_call,
                )
            )

        # Coherencia de niveles: compra → SL < entrada < TP; venta → TP < entrada < SL.
        # Sin esto, un TP del lado equivocado pasaría el filtro R/R (usa distancias).
        is_buy = stop_loss < entry
        if not ((is_buy and entry < take_profit) or (not is_buy and take_profit < entry < stop_loss)):
            return _reject(
                "INCONSISTENT_LEVELS",
                "Los niveles propuestos no son coherentes: el stop loss y el take profit "
                "deben quedar a lados opuestos de la entrada.",
            )

        # La entrada no puede alejarse del precio actual más de N × ATR
        max_distance = self._max_entry_distance(features, current_price)
        if abs(entry - current_price) > max_distance:
            return _reject(
                "ENTRY_TOO_FAR",
                f"La entrada {entry:.8g} está demasiado lejos del precio actual "
                f"{current_price:.8g} (máximo {max_distance:.8g}).",
            )

        # ----------------------------------------------------------
        # Cálculo de posición (Python, no el LLM) en Decimal
        # position_size = (capital × risk_pct) / |entry − stop_loss|
        # ----------------------------------------------------------
        d_entry, d_sl, d_tp = Decimal(str(entry)), Decimal(str(stop_loss)), Decimal(str(take_profit))
        price_risk = abs(d_entry - d_sl)

        if price_risk <= Decimal("0"):
            return ServiceResult.fail(
                code="AGENT_INVALID_PRICE_RISK", http_status=422
            )

        size = Decimal(str(capital)) * Decimal(str(effective_risk_pct)) / price_risk
        # Sin apalancamiento (spot y perpetuos a 1x): la posición nunca vale
        # más que el capital. Con un stop muy cerca de la entrada la regla del
        # 1 % pediría más; se recorta y el riesgo real queda por debajo del 1 %.
        if d_entry > 0:
            size = min(size, Decimal(str(capital)) / d_entry)
        position_size = float(size)

        # ----------------------------------------------------------
        # Fase 4: Filtro R/R (Python determinístico)
        # reward / risk >= min_rr_ratio
        # ----------------------------------------------------------
        reward = abs(d_tp - d_entry)
        rr_ratio = float(reward / price_risk)
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
                    confidence=_confidence(llm_data.get("confidence")),
                    regime_check_passed=True,
                    rules_check_passed=True,
                    rr_check_passed=False,
                    rules_detail=rules_detail,
                    meta=self._build_meta(
                        symbol=symbol, timeframe=timeframe, strategy=strategy,
                        account=account, capital=capital, current_price=current_price,
                        features=features, regime=regime,
                    ),
                    **llm_call,
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
                reasoning=str(llm_data.get("reasoning", ""))[:1000],
                confidence=_confidence(llm_data.get("confidence")),
                regime_check_passed=True,
                rules_check_passed=True,
                rr_check_passed=True,
                rules_detail=rules_detail,
                meta=self._build_meta(
                    symbol=symbol, timeframe=timeframe, strategy=strategy,
                    account=account, capital=capital, current_price=current_price,
                    features=features, regime=regime,
                ),
                **llm_call,
            )
        )

    # ==================================================================
    # Helpers privados
    # ==================================================================

    def _max_entry_distance(self, features: dict, current_price: float) -> float:
        """
        Distancia máxima permitida entre la entrada y el precio actual:
        N × ATR(14), o 2 % del precio si el conjunto no calcula ATR.
        """
        atr = _positive_price(features.get("atr_14"))
        if atr is not None:
            return self._max_entry_atr_distance * atr
        return 0.02 * current_price

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
            passed, actual = evaluate_rule(rule, features)
            details.append(
                RuleCheckDetail(
                    indicator=rule.get("indicator", ""),
                    operator=rule.get("operator", ""),
                    threshold=rule.get("value"),
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
            data = json.loads(cleaned, parse_constant=_reject_json_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMParseError(raw_response=raw, detail=str(exc)) from exc

        if not isinstance(data, dict):
            raise LLMParseError(
                raw_response=raw,
                detail="La respuesta del LLM no es un objeto JSON.",
            )

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
        risk_pct: float,
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

        # Solo los indicadores que calcula el conjunto del bot: clave que
        # debe existir → línea del prompt
        indicator_lines: list[tuple[str, str]] = [
            ("rsi_14", f"RSI(14):   {_fmt(features.get('rsi_14'), 2)}"),
            ("ema_20", f"EMA(20):   {_fmt(features.get('ema_20'), 4)}"),
            ("ema_50", f"EMA(50):   {_fmt(features.get('ema_50'), 4)}"),
            ("ema_200", f"EMA(200):  {_fmt(features.get('ema_200'), 4)}"),
            ("macd", (
                f"MACD:      {_fmt(features.get('macd'), 4)} | "
                f"Signal: {_fmt(features.get('macd_signal'), 4)} | "
                f"Hist: {_fmt(features.get('macd_hist'), 4)}"
            )),
            ("atr_14", f"ATR(14):   {_fmt(features.get('atr_14'), 4)}"),
            ("bb_upper", (
                f"BB Upper:  {_fmt(features.get('bb_upper'), 4)} | "
                f"Mid: {_fmt(features.get('bb_mid'), 4)} | "
                f"Lower: {_fmt(features.get('bb_lower'), 4)}"
            )),
            ("vol_rel", f"Vol Rel:   {_fmt(features.get('vol_rel'), 2)}x"),
        ]
        indicators_text = "\n".join(
            line for key, line in indicator_lines if key in features
        ) or "  (no indicators)"

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
            f"{indicators_text}\n\n"
            f"=== STRATEGY RULES (all passed) ===\n"
            f"{rules_text or '  (no rules defined)'}\n\n"
            f"=== ACCOUNT ===\n"
            f"Capital:    {_fmt(capital, 2)} {base_currency}\n"
            f"Risk/Trade: {risk_pct * 100:.1f}%\n\n"
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
                if k in features
            },
        }
