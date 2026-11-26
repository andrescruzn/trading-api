# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/signals/generate_signal_service.py
#
# Genera una señal de trading para un bot invocando el Agente (M6).
#
# FLUJO:
#   1. Carga el bot por ID y valida que esté activo.
#   2. Invoca AnalyzeService con los datos del bot (symbol, timeframe,
#      strategy, account, feature_set).
#   3. Mapea el AnalysisResult → Signal entity.
#   4. Persiste la Signal en la BD. Si el agente está en modo approval/auto
#      y la señal es BUY/SELL aprobada, queda `pending` hasta expires_at.
#   5. Hooks: alertas, aviso de aprobación (Telegram) y reparto a los
#      suscriptores de un agente compartido — nunca bloquean.
#
# INTEGRACIÓN CON EL AGENTE (M6):
#   El AnalyzeService se recibe como dependencia ya construida por el
#   BotServiceFactory, que le inyecta todos sus repos necesarios.
#   Este servicio no conoce los detalles internos del agente.
# ======================================================================

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.agent.services.agent.analyze_service import AnalyzeService
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.fund_capital_port import FundCapitalPort
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_entity import Signal
from app.common.utils import utc_now
from app.modules.bots.domain.signal_repository import SignalRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot

# TYPE_CHECKING para evitar import circular — se resuelve en runtime
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from app.modules.alerts.services.evaluation.evaluate_alerts_service import EvaluateAlertsService


logger = logging.getLogger(__name__)


class GenerateSignalService:
    """
    Genera y persiste una señal de trading para un bot.

    Reglas de negocio:
    - El bot debe estar en estado 'running' para generar señales.
    - Una señal hold no tiene precios (entry/SL/TP son None).
    - El campo 'approved' refleja si pasó todos los filtros del Agente.
    - El campo 'reasons' persiste el resultado completo del análisis
      para auditoría y trazabilidad.
    """

    def __init__(
        self,
        bot_repo: BotRepository,
        signal_repo: SignalRepository,
        analyze_service: AnalyzeService,
        account_repo: AccountRepository,
        evaluate_alerts: "EvaluateAlertsService | None" = None,
        notify_pending: "Callable[[Signal, Bot], None] | None" = None,
        approval_ttl_minutes: int = 60,
        notify_subscribers: "Callable[[Signal, Bot], object] | None" = None,
        fund_capital: FundCapitalPort | None = None,
    ):
        self._notify_pending = notify_pending
        self._notify_subscribers = notify_subscribers
        self._approval_ttl_minutes = approval_ttl_minutes
        self._account_repo = account_repo
        self._bot_repo = bot_repo
        self._signal_repo = signal_repo
        self._analyze = analyze_service
        self._evaluate_alerts = evaluate_alerts
        self._fund_capital = fund_capital

    def generate(
        self,
        bot_id: int,
        owner_id: int | None = None,
        candle_ts: datetime | None = None,
    ) -> ServiceResult[Signal]:
        """
        Genera y persiste una señal del bot.

        Args:
            owner_id:  None = sin restricción (admin o scheduler).
            candle_ts: vela cerrada que dispara la señal automática (scheduler).
                       Se guarda para no repetir la misma vela.
        """
        # ------------------------------------------------------------------
        # 1. Cargar y validar el bot (un usuario solo opera los suyos)
        # ------------------------------------------------------------------
        bot = find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        if not bot.is_active():
            return ServiceResult.fail(
                code="BOT_NOT_ACTIVE",
                http_status=409,
                meta={"status": bot.status},
            )

        # ------------------------------------------------------------------
        # 2. Invocar el Agente (Prompt Maestro M6)
        #    Usa el feature_set_id configurado en el bot.
        # ------------------------------------------------------------------
        if bot.feature_set_id is None:
            return ServiceResult.fail(code="BOT_NO_FEATURE_SET", http_status=422)

        analysis_result = self._analyze.analyze(
            symbol_id=bot.symbol_id,
            timeframe_id=bot.timeframe_id,
            strategy_id=bot.strategy_id,
            account_id=bot.account_id,
            feature_set_id=bot.feature_set_id,
            risk_pct=bot.effective_risk_pct,
            as_of=candle_ts,
            # Fondo común: el 1 % se calcula sobre el capital del agente, no
            # sobre el saldo de la billetera (que es de todos)
            capital=self._fund_capital_of(bot),
        )

        if not analysis_result.success:
            # Error técnico del agente (LLM caído, sin datos, etc.)
            return ServiceResult.fail(
                code=analysis_result.error.code,
                http_status=analysis_result.error.http_status,
                meta=analysis_result.error.meta,
            )

        result = analysis_result.data
        approved = result.approved

        # ------------------------------------------------------------------
        # 3. Determinar acción: APPROVED → buy o sell según la estrategia,
        #    REJECTED → hold (no operar)
        # ------------------------------------------------------------------
        # La dirección (buy/sell) la define el LLM via el reasoning.
        # Usamos la decisión final para determinar la acción.
        if approved:
            # El agente no devuelve explícitamente buy/sell en este diseño:
            # inferimos del precio vs stop_loss (entry > SL → buy, entry < SL → sell)
            if result.entry is not None and result.stop_loss is not None:
                action = "buy" if result.entry > result.stop_loss else "sell"
            else:
                action = "hold"
        else:
            action = "hold"

        # ------------------------------------------------------------------
        # 4. Construir la entidad Signal
        # ------------------------------------------------------------------
        reasons = result.to_dict()

        # Hash de features para trazabilidad (fingerprint del contexto de mercado)
        features_snapshot = result.meta.get("features_snapshot", {})
        features_hash = hashlib.sha256(
            json.dumps(features_snapshot, sort_keys=True).encode()
        ).hexdigest()[:64]

        signal = Signal(
            id=0,
            bot_id=bot_id,
            ts=utc_now(),
            action=action,
            approved=approved,
            reasons=reasons,
            confidence=Decimal(str(result.confidence)) if result.confidence is not None else None,
            entry_price=Decimal(str(result.entry)) if result.entry is not None else None,
            stop_loss=Decimal(str(result.stop_loss)) if result.stop_loss is not None else None,
            take_profit=Decimal(str(result.take_profit)) if result.take_profit is not None else None,
            position_size=Decimal(str(result.position_size)) if result.position_size is not None else None,
            rr_ratio=Decimal(str(result.rr_ratio)) if result.rr_ratio is not None else None,
            features_hash=features_hash,
            llm_provider=result.llm_provider,
            llm_model=result.llm_model,
            llm_latency_ms=result.llm_latency_ms,
            candle_ts=candle_ts,
        )

        # ------------------------------------------------------------------
        # 4b. Decisión de ejecución: en approval/auto una BUY/SELL aprobada
        #     queda pendiente (de la persona o del ejecutor automático)
        # ------------------------------------------------------------------
        if signal.is_actionable() and bot.is_automated():
            signal.decision_status = "pending"
            signal.expires_at = signal.ts + timedelta(
                minutes=bot.approval_ttl_minutes or self._approval_ttl_minutes
            )

        # ------------------------------------------------------------------
        # 5. Persistir
        # ------------------------------------------------------------------
        created = self._signal_repo.create(signal)
        self._signal_repo.commit()

        # ------------------------------------------------------------------
        # 6. Hook de alertas (fire-and-forget — no revierte si falla)
        # ------------------------------------------------------------------
        if self._evaluate_alerts is not None:
            try:
                self._evaluate_alerts.evaluate_signal_alerts(
                    signal=created, bot_id=bot_id
                )
            except Exception:
                pass  # Las alertas nunca bloquean la operación principal

        # ------------------------------------------------------------------
        # 7. Aviso de aprobación (Telegram con botones) — fire-and-forget
        # ------------------------------------------------------------------
        if created.is_pending() and bot.execution_mode == "approval" and self._notify_pending:
            try:
                self._notify_pending(created, bot)
            except Exception:
                logger.exception("No se pudo avisar la señal pendiente %s", created.id)

        # ------------------------------------------------------------------
        # 8. Señal compartida (Telegram, sin botones) a quienes siguen el
        #    agente — solo BUY/SELL aprobadas; fire-and-forget
        # ------------------------------------------------------------------
        if bot.share_signals and created.is_actionable() and self._notify_subscribers:
            try:
                self._notify_subscribers(created, bot)
            except Exception:
                logger.exception("No se pudo repartir la señal compartida %s", created.id)

        return ServiceResult.ok(data=created)

    def _fund_capital_of(self, bot: Bot) -> Decimal | None:
        """Capital del agente en el fondo común, o None si el fondo no lo maneja."""
        if self._fund_capital is None:
            return None
        fund = self._fund_capital.capital_for(bot)
        return None if fund is None else fund.capital
