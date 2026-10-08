# -*- coding: utf-8 -*-

# ======================================================================
# seeds/accounts.py
#
# PROPÓSITO:
# - Cuentas paper de ejemplo del Módulo 4 (Binance y Bybit) con balances
#   iniciales, para desarrollo y pruebas.
#
# NOTAS:
# - Requiere que el usuario DEMO_USER_EMAIL ya exista (registrado desde la
#   web) y que se haya corrido el seed `market_data`. Si falta, se omite.
# - Clave natural: cuenta = (user_id, name); balance = (account_id, asset).
#   La tabla no tiene UNIQUE para esto (en balances el UNIQUE incluye `ts`),
#   por eso el .sql anterior con INSERT IGNORE duplicaba filas.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.infrastructure.account_balance_model import AccountBalanceModel
from app.modules.accounts.infrastructure.account_model import AccountModel
from app.modules.market.infrastructure.exchange_model import ExchangeModel
from app.modules.users.infrastructure.user_model import UserModel
from seeds._helpers import SeedStats, get_or_create

DEMO_USER_EMAIL = "andrescruznovoa@gmail.com"

# (exchange, nombre de la cuenta, nota, [(asset, free)])
ACCOUNTS: list[tuple[str, str, str, list[tuple[str, Decimal]]]] = [
    (
        "Binance",
        "Binance Paper — Demo",
        "Cuenta de simulación para desarrollo",
        [("USDT", Decimal("10000")), ("BTC", Decimal("0.25"))],
    ),
    (
        "Bybit",
        "Bybit Paper — Demo",
        "Cuenta de simulación Bybit",
        [("USDT", Decimal("5000"))],
    ),
]


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    user = session.execute(
        select(UserModel).filter_by(email=DEMO_USER_EMAIL)
    ).scalar_one_or_none()
    if user is None:
        stats.notes.append(f"omitido: no existe el usuario {DEMO_USER_EMAIL}")
        return stats

    for exchange_name, account_name, note, balances in ACCOUNTS:
        exchange = session.execute(
            select(ExchangeModel).filter_by(name=exchange_name)
        ).scalar_one_or_none()
        if exchange is None:
            stats.notes.append(f"omitida '{account_name}': falta el exchange {exchange_name}")
            continue

        account = get_or_create(
            session,
            AccountModel,
            lookup={"user_id": user.id, "name": account_name},
            values={
                "exchange_id": exchange.id,
                "mode": "paper",
                "base_currency": "USDT",
                "status": "active",
                "credentials_ref": None,
                "meta": {"note": note},
            },
            stats=stats,
        )

        for asset, free in balances:
            get_or_create(
                session,
                AccountBalanceModel,
                lookup={"account_id": account.id, "asset": asset},
                values={"free": free, "locked": Decimal("0")},
                stats=stats,
            )

    return stats
