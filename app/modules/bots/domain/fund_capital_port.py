# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/fund_capital_port.py
#
# PROPÓSITO:
# - Contrato con el fondo común (M11) para saber con cuánto dinero opera un
#   agente. Lo implementa el módulo `fund`; lo usan la generación de señales
#   (regla del 1 %) y el RiskGate de M8 (drawdown máximo).
#
# DECISIÓN:
# - Puerto en el dominio de bots (inversión de dependencias): bots y orders
#   no importan el módulo fund; el provider inyecta la implementación.
# - `None` = el fondo no maneja este agente (cuenta de práctica u otra
#   cuenta): se usa el saldo libre de su cuenta, como siempre.
# - Un agente sobre la billetera de la plataforma sin pool devuelve capital
#   0: no puede arriesgar el dinero de todos por fuera de la contabilidad
#   del fondo (decisión del 2026-10-23).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.modules.bots.domain.bot_entity import Bot


@dataclass(frozen=True)
class FundCapital:
    """
    capital         → base de la regla del 1 %: equity de la última liquidación
                      + resultado desde entonces (lo abierto, a precio de costo).
    settled_equity  → equity de la última liquidación (base del drawdown).
    """

    capital: Decimal
    settled_equity: Decimal


class FundCapitalPort(Protocol):

    def capital_for(self, bot: Bot) -> FundCapital | None:
        """Capital del agente en el fondo, o None si el fondo no lo maneja."""
        ...
