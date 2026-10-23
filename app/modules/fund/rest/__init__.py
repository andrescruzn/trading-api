# -*- coding: utf-8 -*-

from .deposits.routes import router as fund_deposits_router
from .fees.routes import router as fund_fees_router
from .ledger.routes import router as fund_ledger_router
from .payouts.routes import router as fund_payouts_router
from .pools.routes import router as fund_pools_router
from .settings.routes import router as fund_settings_router

__all__ = [
    "fund_deposits_router",
    "fund_fees_router",
    "fund_ledger_router",
    "fund_payouts_router",
    "fund_pools_router",
    "fund_settings_router",
]
