# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/execution/executor_interface.py
#
# Interfaz (ABC) del ejecutor de órdenes — Patrón Strategy.
#
# Define el contrato que deben cumplir PaperExecutor y LiveExecutor.
# El CreateOrderService depende de esta abstracción, no de la
# implementación concreta, permitiendo intercambiar paper/live
# sin modificar la lógica del servicio.
#
# RESULTADO:
# - `ExecutionResult.status` es lo que reporta el exchange, no lo que
#   suponemos: `filled`, `partially_filled` o `sent` (aceptada pero aún
#   sin ejecutar, p. ej. una límite lejos del precio). Solo hay `fill`
#   cuando se ejecutó algo.
#
# ERRORES:
# - RuntimeError: el exchange rechazó la orden o no se pudo enviar (la
#   orden no existe allí) → se marca `rejected`.
# - ExecutionUncertainError: no sabemos si llegó (timeout de red) → la
#   orden queda `sent` con `needs_reconciliation` para revisarla.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.order_entity import Order


class ExecutionUncertainError(RuntimeError):
    """La orden pudo llegar o no al exchange: hay que reconciliarla."""


@dataclass
class ExecutionResult:
    status: str                       # filled | partially_filled | sent
    exchange_order_id: str | None = None
    fill: Fill | None = None


class ExecutorInterface(ABC):
    """
    Contrato para ejecutar una orden.

    El ejecutor recibe la orden y el bot completo (para acceder
    a account_id, mode y otros datos de contexto) y retorna
    el resultado real de la ejecución.

    Implementaciones:
    - PaperExecutor : simula la ejecución con el último precio de vela
    - LiveExecutor  : envía la orden al exchange real via ccxt
    """

    @abstractmethod
    def execute(self, order: Order, bot: Bot) -> ExecutionResult:
        """
        Ejecuta la orden y retorna su resultado.

        Args:
            order: La orden a ejecutar (ya persistida, con client_order_id).
            bot:   El bot propietario de la orden (para modo, account, symbol).

        Raises:
            ExecutionUncertainError: si no se sabe si la orden llegó.
            RuntimeError: si la ejecución falla y la orden no existe en el exchange.
        """
        ...
