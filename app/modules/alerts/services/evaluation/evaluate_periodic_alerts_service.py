# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/services/evaluation/evaluate_periodic_alerts_service.py
#
# CASO DE USO:
# - Revisar las reglas activas `price`, `pnl` y `drawdown` (paso del ciclo
#   de ejecución del scheduler) y disparar las que se cumplen.
# - `evaluate_price(symbol_id, price)`: evaluación manual de precio con un
#   precio dado (POST /api/alerts/evaluate, admin).
#
# REGLAS (rule_spec):
# - price:    {symbol_id, operator: lt|lte|gt|gte, threshold} → último
#             cierre del símbolo (la vela más reciente en BD, de cualquier
#             timeframe) frente al umbral.
# - pnl:      {threshold (%), period: daily|total} → P&L del agente en %
#             del capital invertido (domain/rule_conditions.py). `daily` =
#             lo ganado o perdido desde las 00:00 hora de Bogotá.
# - drawdown: {threshold (%)} → caída actual desde el mejor P&L acumulado.
# - pnl y drawdown necesitan un agente (`bot_id`); sin él se omiten.
#
# ANTISPAM:
# - Si el último evento de la regla tiene menos de ALERT_REPEAT_MINUTES,
#   la regla no se evalúa: mientras la condición siga, el aviso se repite
#   como máximo una vez por ventana.
#
# ERRORES:
# - Aislados por regla (log + rollback): una regla rota no frena a otras.
# ======================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from app.common.contracts import ServiceResult
from app.common.utils import ensure_aware_utc, utc_now, utc_to_bogota
from app.modules.alerts.channels.alert_messages import (
    drawdown_alert_text,
    pnl_alert_text,
    price_alert_text,
)
from app.modules.alerts.domain.alert_event_repository import AlertEventRepository
from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.domain.alert_rule_repository import AlertRuleRepository
from app.modules.alerts.domain.rule_conditions import (
    PERIODIC_RULE_TYPES,
    PRICE_OPERATORS,
    BotPnlSnapshot,
    bot_pnl_snapshot,
    daily_pnl_pct,
    drawdown_condition_met,
    in_cooldown,
    pnl_condition_met,
    price_condition_met,
)
from app.modules.alerts.services.evaluation.fire_alert_service import FireAlertService
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.performance import TradeFill, compute_performance

logger = logging.getLogger(__name__)

_ONE_MICROSECOND = timedelta(microseconds=1)


@dataclass
class PeriodicAlertsReport:
    checked: int = 0     # reglas revisadas
    fired: int = 0       # alertas disparadas
    cooldown: int = 0    # omitidas: avisaron hace menos de ALERT_REPEAT_MINUTES
    skipped: int = 0     # sin datos (sin velas, sin agente, sin operaciones, spec inválida)
    failed: int = 0      # error inesperado (logueado)


@dataclass(frozen=True)
class _Trigger:
    title: str
    message: str
    severity: str
    payload: dict[str, Any]


class _NoData(Exception):
    """La regla no se puede evaluar todavía (sin velas, agente u operaciones)."""


class EvaluatePeriodicAlertsService:
    """Evalúa las reglas de precio, P&L y drawdown con los datos ya guardados."""

    def __init__(
        self,
        *,
        rule_repo: AlertRuleRepository,
        event_repo: AlertEventRepository,
        fire_service: FireAlertService,
        candle_repo: CandleRepository,
        timeframe_repo: TimeframeRepository,
        symbol_repo: SymbolRepository,
        bot_repo: BotRepository,
        fill_repo: FillRepository,
        repeat_minutes: int,
        clock: Callable[[], datetime] = utc_now,
    ):
        self._rule_repo = rule_repo
        self._event_repo = event_repo
        self._fire = fire_service
        self._candle_repo = candle_repo
        self._timeframe_repo = timeframe_repo
        self._symbol_repo = symbol_repo
        self._bot_repo = bot_repo
        self._fill_repo = fill_repo
        self._repeat_minutes = repeat_minutes
        self._clock = clock

    # ------------------------------------------------------------------
    # Ciclo del scheduler
    # ------------------------------------------------------------------

    def run(self) -> ServiceResult[PeriodicAlertsReport]:
        report = PeriodicAlertsReport()
        now = self._clock()
        cache: dict[tuple, Any] = {}

        for rule_type in PERIODIC_RULE_TYPES:
            for rule in self._rule_repo.list_active_by_type_and_bot(rule_type=rule_type):
                self._process(
                    rule, report, now, lambda r=rule: self._evaluate(r, now, cache)
                )
        return ServiceResult.ok(report)

    # ------------------------------------------------------------------
    # Endpoint manual (admin)
    # ------------------------------------------------------------------

    def evaluate_price(
        self, symbol_id: int, current_price: Decimal
    ) -> ServiceResult[PeriodicAlertsReport]:
        """Reglas `price` del símbolo contra un precio dado (mismo antispam)."""
        report = PeriodicAlertsReport()
        now = self._clock()
        for rule in self._rule_repo.list_active_by_type_and_bot(rule_type="price"):
            if _spec_int(rule.rule_spec, "symbol_id") != symbol_id:
                continue
            self._process(
                rule, report, now,
                lambda r=rule: self._price_trigger(r, Decimal(str(current_price)), None),
            )
        return ServiceResult.ok(report)

    # ------------------------------------------------------------------
    # Orquestación por regla
    # ------------------------------------------------------------------

    def _process(
        self,
        rule: AlertRule,
        report: PeriodicAlertsReport,
        now: datetime,
        evaluate: Callable[[], _Trigger | None],
    ) -> None:
        report.checked += 1
        try:
            last = self._event_repo.get_last_by_rule(rule.id)
            if in_cooldown(last.ts if last else None, now, self._repeat_minutes):
                report.cooldown += 1
                return

            trigger = evaluate()
            if trigger is None:
                return

            self._fire.fire(
                rule=rule,
                title=trigger.title,
                message=trigger.message,
                severity=trigger.severity,
                payload=trigger.payload,
            )
            report.fired += 1
        except _NoData:
            report.skipped += 1
        except Exception:
            report.failed += 1
            logger.exception("[Alerts] Error evaluando la regla %s (%s)", rule.id, rule.rule_type)
            try:
                self._rule_repo.rollback()
            except Exception:
                logger.exception("[Alerts] Rollback falló tras la regla %s", rule.id)

    def _evaluate(
        self, rule: AlertRule, now: datetime, cache: dict[tuple, Any]
    ) -> _Trigger | None:
        if rule.rule_type == "price":
            symbol_id = _spec_int(rule.rule_spec, "symbol_id")
            if symbol_id is None:
                raise _NoData
            latest = self._cached(
                cache, ("price", symbol_id), lambda: self._latest_price(symbol_id)
            )
            if latest is None:
                raise _NoData
            price, candle_ts = latest
            return self._price_trigger(rule, price, candle_ts)

        bot = self._cached(cache, ("bot", rule.bot_id), lambda: self._load_bot(rule.bot_id))
        fills = self._cached(cache, ("fills", bot.id), lambda: self._load_fills(bot.id))
        if rule.rule_type == "pnl":
            return self._pnl_trigger(rule, bot, fills, now, cache)
        return self._drawdown_trigger(rule, bot, fills, cache)

    # ------------------------------------------------------------------
    # Precio
    # ------------------------------------------------------------------

    def _price_trigger(
        self, rule: AlertRule, price: Decimal, candle_ts: datetime | None
    ) -> _Trigger | None:
        operator = rule.rule_spec.get("operator", "lt")
        threshold = _spec_decimal(rule.rule_spec, "threshold")
        symbol_id = _spec_int(rule.rule_spec, "symbol_id")
        if operator not in PRICE_OPERATORS or threshold is None or symbol_id is None:
            raise _NoData
        if not price_condition_met(price, operator, threshold):
            return None

        symbol = self._symbol_repo.get_by_id(symbol_id)
        title, message = price_alert_text(
            symbol=symbol.symbol if symbol else f"Símbolo {symbol_id}",
            quote_asset=symbol.quote_asset if symbol else "",
            operator=operator,
            threshold=threshold,
            price=price,
        )
        payload: dict[str, Any] = {
            "symbol_id": symbol_id,
            "current_price": float(price),
            "threshold": float(threshold),
            "operator": operator,
        }
        if candle_ts is not None:
            payload["candle_ts"] = ensure_aware_utc(candle_ts).isoformat()
        return _Trigger(title, message, "warning", payload)

    def _latest_price(self, symbol_id: int) -> tuple[Decimal, datetime] | None:
        """Cierre de la vela más reciente del símbolo entre todos los timeframes."""
        latest = None
        for timeframe in self._timeframe_repo.list_all():
            candles = self._candle_repo.list_candles(
                symbol_id=symbol_id, timeframe_id=timeframe.id, limit=1
            )
            if not candles:
                continue
            if latest is None or ensure_aware_utc(candles[0].ts) > ensure_aware_utc(latest.ts):
                latest = candles[0]
        return (Decimal(str(latest.close)), latest.ts) if latest is not None else None

    # ------------------------------------------------------------------
    # P&L
    # ------------------------------------------------------------------

    def _pnl_trigger(
        self,
        rule: AlertRule,
        bot: Bot,
        fills: list[TradeFill],
        now: datetime,
        cache: dict[tuple, Any],
    ) -> _Trigger | None:
        threshold = _spec_decimal(rule.rule_spec, "threshold")
        period = rule.rule_spec.get("period", "total")
        if threshold is None:
            raise _NoData

        snapshot = self._cached(cache, ("snapshot", bot.id), lambda: self._snapshot(bot, fills))
        if period == "daily":
            day_start = _bogota_day_start(now)
            start = self._cached(
                cache, ("snapshot_day", bot.id), lambda: self._snapshot(bot, fills, until=day_start)
            )
            pnl_pct = daily_pnl_pct(snapshot, start)
            pnl = snapshot.total_pnl - start.total_pnl
        else:
            period = "total"
            pnl_pct = snapshot.pnl_pct
            pnl = snapshot.total_pnl

        if pnl_pct is None:
            raise _NoData
        if not pnl_condition_met(pnl_pct, threshold):
            return None

        title, message = pnl_alert_text(
            agent_name=bot.name,
            period=period,
            pnl_pct=pnl_pct,
            pnl=pnl,
            invested=snapshot.invested,
            threshold=threshold,
            quote_asset=self._quote_asset(bot, cache),
        )
        return _Trigger(
            title,
            message,
            "warning" if threshold < 0 else "info",
            {
                "bot_id": bot.id,
                "period": period,
                "pnl_pct": float(round(pnl_pct, 4)),
                "pnl": float(pnl),
                "invested": float(snapshot.invested),
                "threshold": float(threshold),
            },
        )

    # ------------------------------------------------------------------
    # Drawdown
    # ------------------------------------------------------------------

    def _drawdown_trigger(
        self, rule: AlertRule, bot: Bot, fills: list[TradeFill], cache: dict[tuple, Any]
    ) -> _Trigger | None:
        threshold = _spec_decimal(rule.rule_spec, "threshold")
        if threshold is None:
            raise _NoData

        snapshot = self._cached(cache, ("snapshot", bot.id), lambda: self._snapshot(bot, fills))
        if snapshot.drawdown_pct is None:
            raise _NoData
        if not drawdown_condition_met(snapshot.drawdown_pct, threshold):
            return None

        title, message = drawdown_alert_text(
            agent_name=bot.name,
            drawdown_pct=snapshot.drawdown_pct,
            drawdown=snapshot.drawdown,
            invested=snapshot.invested,
            threshold=threshold,
            quote_asset=self._quote_asset(bot, cache),
        )
        return _Trigger(
            title,
            message,
            "critical",
            {
                "bot_id": bot.id,
                "drawdown_pct": float(round(snapshot.drawdown_pct, 4)),
                "drawdown": float(snapshot.drawdown),
                "invested": float(snapshot.invested),
                "threshold": float(threshold),
            },
        )

    # ------------------------------------------------------------------
    # Datos del agente
    # ------------------------------------------------------------------

    def _load_bot(self, bot_id: int | None) -> Bot:
        bot = self._bot_repo.get_by_id(bot_id) if bot_id is not None else None
        if bot is None:
            raise _NoData
        return bot

    def _load_fills(self, bot_id: int) -> list[TradeFill]:
        return self._fill_repo.list_trade_fills_by_bots([bot_id]).get(bot_id, [])

    def _snapshot(
        self, bot: Bot, fills: list[TradeFill], until: datetime | None = None
    ) -> BotPnlSnapshot:
        """P&L con los fills hasta `until` (excluido) y el último cierre hasta ese momento."""
        if until is not None:
            fills = [f for f in fills if f.ts is not None and ensure_aware_utc(f.ts) < until]
        candles = self._candle_repo.list_candles(
            symbol_id=bot.symbol_id,
            timeframe_id=bot.timeframe_id,
            to_ts=until - _ONE_MICROSECOND if until is not None else None,
            limit=1,
        )
        last_price = Decimal(str(candles[0].close)) if candles else None
        return bot_pnl_snapshot(compute_performance(fills), last_price)

    def _quote_asset(self, bot: Bot, cache: dict[tuple, Any]) -> str:
        symbol = self._cached(
            cache, ("symbol", bot.symbol_id), lambda: self._symbol_repo.get_by_id(bot.symbol_id)
        )
        return symbol.quote_asset if symbol else ""

    @staticmethod
    def _cached(cache: dict[tuple, Any], key: tuple, load: Callable[[], Any]) -> Any:
        if key not in cache:
            cache[key] = load()
        return cache[key]


# ======================================================================
# Helpers
# ======================================================================

def _spec_decimal(spec: dict[str, Any], key: str) -> Decimal | None:
    value = spec.get(key)
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _spec_int(spec: dict[str, Any], key: str) -> int | None:
    value = spec.get(key)
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bogota_day_start(now: datetime) -> datetime:
    """00:00 de hoy en Bogotá, en UTC (el día que ve la persona en la app)."""
    local = utc_to_bogota(now)
    return ensure_aware_utc(local.replace(hour=0, minute=0, second=0, microsecond=0))
