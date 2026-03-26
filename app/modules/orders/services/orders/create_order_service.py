# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/create_order_service.py
#
# Crea y ejecuta una orden de trading — lógica central del Módulo 8.
#
# FLUJO COMPLETO:
#   1. Validar bot (existe, está running, tiene cuenta)
#   2. Validar parámetros de la orden (side, type, qty, price)
#   3. Crear la entidad Order (status="new")
#   4. Persistir la orden en BD (para obtener order.id)
#   5. Seleccionar executor según bot.mode (paper o live)
#   6. executor.execute(order, bot) → Fill
#   7. Persistir el Fill
#   8. Actualizar order.status = "filled"
#   9. Upsert Position (crear si no existe, actualizar si ya existe)
#  10. session.commit() único — todo o nada
#  11. Retornar ServiceResult.ok(data=order)
#
# DECISIÓN DE DISEÑO — Atomicidad:
#   Todo ocurre en una sola transacción. Si el executor falla
#   (ej: exchange rechaza la orden), hacemos session.rollback()
#   implícito ya que no se llama commit().
#   Así nunca queda una Order en BD sin su Fill correspondiente.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.common.utils.datetime_utils import utc_now
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.domain.position_repository import PositionRepository
from app.modules.orders.execution.executor_interface import ExecutorInterface
from app.modules.orders.execution.live_executor import LiveExecutor
from app.modules.orders.execution.paper_executor import PaperExecutor

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.modules.alerts.services.evaluation.evaluate_alerts_service import EvaluateAlertsService


class CreateOrderService:
    """
    Crea y ejecuta una orden de trading.

    Reglas de negocio:
    - El bot debe estar en estado 'running' para aceptar órdenes.
    - side debe ser 'buy' o 'sell' (no 'hold' — hold = no operar).
    - type 'limit' y 'stop_limit' requieren price > 0.
    - type 'stop' y 'stop_limit' requieren stop_price > 0.
    - qty debe ser > 0.
    - La ejecución es atómica: order + fill + position en un commit.
    """

    def __init__(
        self,
        order_repo: OrderRepository,
        fill_repo: FillRepository,
        position_repo: PositionRepository,
        bot_repo: BotRepository,
        symbol_repo: SymbolRepository,
        paper_executor: PaperExecutor,
        live_executor: LiveExecutor,
        session: Session,
        evaluate_alerts: "EvaluateAlertsService | None" = None,
    ):
        self._order_repo = order_repo
        self._fill_repo = fill_repo
        self._position_repo = position_repo
        self._bot_repo = bot_repo
        self._symbol_repo = symbol_repo
        self._paper_executor = paper_executor
        self._live_executor = live_executor
        self._session = session
        self._evaluate_alerts = evaluate_alerts

    def create(
        self,
        bot_id: int,
        side: str,
        order_type: str,
        qty: Decimal,
        price: Decimal | None = None,
        stop_price: Decimal | None = None,
        time_in_force: str | None = None,
        signal_id: int | None = None,
    ) -> ServiceResult[Order]:

        # ------------------------------------------------------------------
        # 1. Cargar y validar el bot
        # ------------------------------------------------------------------
        bot = self._bot_repo.get_by_id(bot_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        if bot.status != "running":
            return ServiceResult.fail(
                code="BOT_NOT_RUNNING",
                http_status=409,
                meta={"status": bot.status},
            )

        # ------------------------------------------------------------------
        # 2. Validar parámetros de la orden
        # ------------------------------------------------------------------
        if side not in Order.VALID_SIDES:
            return ServiceResult.fail(
                code="ORDER_INVALID_SIDE",
                http_status=422,
                meta={"side": side},
            )

        if order_type not in Order.VALID_TYPES:
            return ServiceResult.fail(
                code="ORDER_INVALID_TYPE",
                http_status=422,
                meta={"type": order_type},
            )

        if qty <= Decimal("0"):
            return ServiceResult.fail(code="ORDER_INVALID_QTY", http_status=422)

        # Las órdenes limit y stop_limit requieren price
        if order_type in ("limit", "stop_limit") and (price is None or price <= Decimal("0")):
            return ServiceResult.fail(
                code="ORDER_PRICE_REQUIRED",
                http_status=422,
                meta={"type": order_type},
            )

        # Las órdenes stop y stop_limit requieren stop_price
        if order_type in ("stop", "stop_limit") and (stop_price is None or stop_price <= Decimal("0")):
            return ServiceResult.fail(
                code="ORDER_STOP_PRICE_REQUIRED",
                http_status=422,
                meta={"type": order_type},
            )

        # ------------------------------------------------------------------
        # 3. Obtener el símbolo para guardar en meta (necesario para LiveExecutor)
        # ------------------------------------------------------------------
        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        if symbol is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        now = utc_now()

        # ------------------------------------------------------------------
        # 4. Construir y persistir la Order (status="new", obtener order.id)
        # ------------------------------------------------------------------
        order = Order(
            id=0,
            bot_id=bot_id,
            signal_id=signal_id,
            side=side,
            type=order_type,
            qty=qty,
            status="new",
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            # Guardamos el símbolo en meta para que LiveExecutor pueda usarlo
            meta={"symbol": symbol.symbol, "mode": bot.mode},
            ts=now,
        )

        order = self._order_repo.create(order)

        # ------------------------------------------------------------------
        # 5. Seleccionar executor según el modo del bot (patrón Strategy)
        # ------------------------------------------------------------------
        executor: ExecutorInterface = (
            self._paper_executor if bot.mode == "paper" else self._live_executor
        )

        # ------------------------------------------------------------------
        # 6. Ejecutar la orden → produce un Fill
        #    Si falla, RuntimeError se propaga como error 502
        # ------------------------------------------------------------------
        try:
            fill = executor.execute(order, bot)
        except RuntimeError as exc:
            return ServiceResult.fail(
                code="ORDER_EXECUTION_FAILED",
                http_status=502,
                meta={"detail": str(exc)},
            )

        # Actualizar el order_id del fill (el executor crea el fill con id=0)
        fill.order_id = order.id

        # ------------------------------------------------------------------
        # 7. Persistir el Fill
        # ------------------------------------------------------------------
        fill = self._fill_repo.create(fill)

        # ------------------------------------------------------------------
        # 8. Actualizar el estado de la orden a "filled"
        #    (En esta versión asumimos ejecución total inmediata)
        # ------------------------------------------------------------------
        order.status = "filled"
        order.exchange_order_id = fill.exchange_trade_id
        order = self._order_repo.update(order)

        # ------------------------------------------------------------------
        # 9. Upsert Position: crear si no existe, actualizar si ya existe
        # ------------------------------------------------------------------
        self._upsert_position(
            bot_id=bot_id,
            symbol_id=bot.symbol_id,
            fill_qty=fill.qty,
            fill_price=fill.price,
            side=side,
        )

        # ------------------------------------------------------------------
        # 10. Commit único — confirma order + fill + position en la BD
        # ------------------------------------------------------------------
        self._session.commit()

        # ------------------------------------------------------------------
        # 11. Hook de alertas (fire-and-forget — no revierte si falla)
        # ------------------------------------------------------------------
        if self._evaluate_alerts is not None:
            try:
                self._evaluate_alerts.evaluate_order_alerts(
                    order=order, bot_id=bot_id
                )
            except Exception:
                pass  # Las alertas nunca bloquean la operación principal

        return ServiceResult.ok(data=order)

    # ------------------------------------------------------------------
    # Helper privado
    # ------------------------------------------------------------------

    def _upsert_position(
        self,
        bot_id: int,
        symbol_id: int,
        fill_qty: Decimal,
        fill_price: Decimal,
        side: str,
    ) -> None:
        """
        Crea o actualiza la posición del bot para un símbolo.

        - Si no existe posición: la crea con qty y avg_price del fill.
        - Si ya existe: aplica apply_buy_fill o apply_sell_fill según el side,
          recalculando el precio promedio ponderado (WAP) y el P&L realizado.

        Esta operación usa la lógica de negocio pura definida en Position entity.
        """
        position = self._position_repo.get_by_bot_and_symbol(
            bot_id=bot_id,
            symbol_id=symbol_id,
        )

        if position is None:
            # Primera operación del bot en este símbolo — crear posición nueva
            position = Position(
                id=0,
                bot_id=bot_id,
                symbol_id=symbol_id,
                qty=Decimal("0"),
                avg_price=Decimal("0"),
                realized_pnl=Decimal("0"),
            )

            if side == "buy":
                position.apply_buy_fill(fill_qty, fill_price)
            else:
                position.apply_sell_fill(fill_qty, fill_price)

            self._position_repo.create(position)
        else:
            # Posición existente — aplicar el fill y actualizar
            if side == "buy":
                position.apply_buy_fill(fill_qty, fill_price)
            else:
                position.apply_sell_fill(fill_qty, fill_price)

            self._position_repo.update(position)
