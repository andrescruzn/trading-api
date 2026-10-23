# -*- coding: utf-8 -*-

from .accounts.routes import router as accounts_router
from .balances.routes import router as balances_router
from .wallet.routes import router as wallet_router

__all__ = [
    "accounts_router",
    "balances_router",
    "wallet_router",
]
