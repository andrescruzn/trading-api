# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/fund_notifier.py
#
# PROPÓSITO:
# - Contrato para avisar a las personas de lo que pasa con su dinero
#   (depósitos, liquidaciones, retiros). El fondo solo emite eventos con
#   un código y datos; los textos y los canales (campana, correo,
#   Telegram) viven en el módulo alerts (FundNoticeService).
#
# REGLAS:
# - Se llama DESPUÉS del commit del caso de uso: nunca se avisa de algo
#   que no quedó guardado.
# - Avisar nunca rompe el caso de uso: la implementación se traga y
#   registra sus errores.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

# Códigos de los eventos (los textos están en alerts/channels/fund_messages.py)
FUND_DEPOSIT_CONFIRMED = "FUND_DEPOSIT_CONFIRMED"
FUND_DEPOSIT_REJECTED = "FUND_DEPOSIT_REJECTED"
FUND_DEPOSIT_IN_REVIEW = "FUND_DEPOSIT_IN_REVIEW"
FUND_ALLOCATION_APPLIED = "FUND_ALLOCATION_APPLIED"
FUND_REDEMPTION_APPLIED = "FUND_REDEMPTION_APPLIED"
FUND_WITHDRAWAL_REQUESTED = "FUND_WITHDRAWAL_REQUESTED"
FUND_WITHDRAWAL_PAID = "FUND_WITHDRAWAL_PAID"
FUND_WITHDRAWAL_REJECTED = "FUND_WITHDRAWAL_REJECTED"


@dataclass(frozen=True)
class FundEvent:
    """
    Algo que una persona debe saber.

    - `user_id`: a quién se avisa; None = a todos los super admin.
    - `about_user_id`: de quién trata (p. ej. quién pidió el retiro), para
      que el aviso a los super admin diga su nombre.
    - `data`: valores del mensaje como texto (montos sin formatear).
    """

    code: str
    user_id: int | None = None
    about_user_id: int | None = None
    data: dict[str, str] = field(default_factory=dict)


class FundNotifier(Protocol):
    def notify(self, events: list[FundEvent]) -> None: ...


class NullFundNotifier:
    """No avisa (scripts y pruebas)."""

    def notify(self, events: list[FundEvent]) -> None:
        return None
