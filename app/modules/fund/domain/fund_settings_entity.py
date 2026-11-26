# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/fund_settings_entity.py
#
# Entidad de dominio: FundSettings (ajustes del fondo común).
# Una sola fila: redes de depósito aceptadas con la dirección de la
# billetera, tope de confirmación automática, vencimiento de solicitudes y
# permanencia mínima en un agente antes de poder retirar.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

# Valores por defecto (decisión del 2026-10-23): se usan mientras nadie
# guarde ajustes, y son los defaults de la tabla.
DEFAULT_MIN_HOLD_DAYS = 30
DEFAULT_DEPOSIT_AUTO_CONFIRM_MAX = Decimal("1000")
DEFAULT_DEPOSIT_REQUEST_TTL_HOURS = 72

# Límites de los ajustes (los mismos que valida la ruta)
MAX_MIN_HOLD_DAYS = 365
MAX_DEPOSIT_REQUEST_TTL_HOURS = 720


@dataclass(frozen=True)
class DepositNetworkConfig:
    """
    Red aceptada para depositar (p. ej. TRC20) y la dirección de la billetera
    en esa red. `tag` es el memo que algunas redes exigen.
    """

    network: str
    name: str
    address: str
    tag: str | None = None


@dataclass
class FundSettings:
    min_hold_days: int = DEFAULT_MIN_HOLD_DAYS
    deposit_auto_confirm_max: Decimal = DEFAULT_DEPOSIT_AUTO_CONFIRM_MAX
    deposit_request_ttl_hours: int = DEFAULT_DEPOSIT_REQUEST_TTL_HOURS
    deposit_networks: list[DepositNetworkConfig] = field(default_factory=list)
    updated_by_user_id: int | None = None
    updated_at: datetime | None = None

    def network(self, code: str) -> DepositNetworkConfig | None:
        """La red aceptada con ese código, o None si no se acepta."""
        for item in self.deposit_networks:
            if item.network == code:
                return item
        return None
