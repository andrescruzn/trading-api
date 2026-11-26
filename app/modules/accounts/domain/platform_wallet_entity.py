# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/platform_wallet_entity.py
#
# Entidad de dominio: PlatformWallet.
# La billetera única de la plataforma (fondo común): qué cuenta de
# exchange guarda el dinero de todos y cómo fue su última sincronización.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PlatformWallet:
    """
    Billetera de la plataforma (una sola fila en `platform_wallet`).

    Reglas de negocio:
    - Toda la plataforma usa una sola cuenta de exchange como billetera.
    - `base_asset` es la moneda en que se valora todo (USDT).
    - `last_sync_error` guarda el código del último fallo de sincronización
      (None si la última salió bien): la UI lo muestra a los propietarios.
    """

    account_id: int
    base_asset: str
    last_synced_at: datetime | None = None
    last_sync_error: str | None = None
    updated_by_user_id: int | None = None
    updated_at: datetime | None = None

    def mark_synced(self, ts: datetime) -> None:
        self.last_synced_at = ts
        self.last_sync_error = None

    def mark_sync_failed(self, code: str) -> None:
        self.last_sync_error = code
