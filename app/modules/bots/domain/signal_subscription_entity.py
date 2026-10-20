# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/signal_subscription_entity.py
#
# Entidad de dominio: SignalSubscription.
# Un usuario sigue las señales de un agente compartido por otra persona:
# recibe por Telegram las BUY/SELL aprobadas, sin ejecutar nada.
# ======================================================================

from __future__ import annotations

from datetime import datetime


class SignalSubscription:
    """
    Suscripción de un usuario a las señales de un agente.

    Reglas de negocio (las aplican los servicios de suscripción):
    - Solo se sigue un agente con `share_signals = True`.
    - Nadie se suscribe a su propio agente.
    - Una sola suscripción por (agente, usuario).
    """

    def __init__(
        self,
        id: int,
        bot_id: int,
        user_id: int,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.bot_id = bot_id
        self.user_id = user_id
        self.created_at = created_at
