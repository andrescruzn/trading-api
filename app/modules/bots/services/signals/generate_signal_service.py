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
#   4. Persiste la Signal en la BD.
#
# INTEGRACIÓN CON EL AGENTE (M6):
#   El AnalyzeService se recibe como dependencia ya construida por el
#   BotServiceFactory, que le inyecta todos sus repos necesarios.
#   Este servicio no conoce los detalles internos del agente.
# ======================================================================

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.agent.services.agent.analyze_service import AnalyzeService
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_repository import SignalRepository


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
        session: Session,
    ):
        self._bot_repo = bot_repo
        self._signal_repo = signal_repo
        self._analyze = analyze_service
        self._session = session

    def generate(self, bot_id: int) -> ServiceResult[Signal]:
        # ------------------------------------------------------------------
        # 1. Cargar y validar el bot
        # ------------------------------------------------------------------
        bot = self._bot_repo.get_by_id(bot_id)
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
            ts=datetime.now(tz=timezone.utc),
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
        )

        # ------------------------------------------------------------------
        # 5. Persistir
        # ------------------------------------------------------------------
        created = self._signal_repo.create(signal)
        self._session.commit()
        return ServiceResult.ok(data=created)
