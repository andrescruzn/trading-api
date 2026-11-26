# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/accounts.py
#
# PROPÓSITO:
# - Billetera única de la plataforma (Módulo 4): la cuenta live
#   "Billetera Binance" y la fila de `platform_wallet`. Es lo mismo que
#   hace la app sola la primera vez que alguien la necesita; el seed solo
#   la deja lista desde el principio.
#
# NOTAS:
# - Requiere el seed `market_data` (exchange Binance) y al menos un super
#   admin activo (seed `users`). Si falta algo, se omite con una nota.
# - Las credenciales no se siembran: van en el `.env` (BINANCE_API_KEY /
#   BINANCE_API_SECRET).
# - Ya no hay cuentas de práctica por usuario: cada agente demo crea la
#   suya (seed `bots`).
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.accounts.infrastructure import SqlAlchemyPlatformWalletRepository
from app.modules.accounts.providers import build_platform_wallet_ensurer
from database.seeds._helpers import SeedStats


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    existed = SqlAlchemyPlatformWalletRepository(session).get() is not None
    account = build_platform_wallet_ensurer(session).ensure()
    if account is None:
        stats.notes.append("omitida la billetera: falta el exchange Binance o un super admin activo")
        return stats

    stats.track("platform_wallet", created=not existed)
    return stats
