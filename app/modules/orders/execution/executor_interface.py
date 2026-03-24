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
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.bots.domain.bot_entity import Bot
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.order_entity import Order


class ExecutorInterface(ABC):
    """
    Contrato para ejecutar una orden y producir un Fill.

    El ejecutor recibe la orden y el bot completo (para acceder
    a account_id, mode y otros datos de contexto) y retorna
    el Fill resultante de la ejecución.

    Implementaciones:
    - PaperExecutor : simula la ejecución con el último precio de vela
    - LiveExecutor  : envía la orden al exchange real via ccxt
    """

    @abstractmethod
    def execute(self, order: Order, bot: Bot) -> Fill:
        """
        Ejecuta la orden y retorna el Fill resultante.

        Args:
            order: La orden a ejecutar (status debe ser "new").
            bot:   El bot propietario de la orden (para modo, account, symbol).

        Returns:
            Fill con precio de ejecución, cantidad y comisión.

        Raises:
            RuntimeError: si la ejecución falla y no puede completarse.
        """
        ...
