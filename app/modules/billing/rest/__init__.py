# -*- coding: utf-8 -*-

from app.modules.billing.rest.investors.routes import router as investors_router
from app.modules.billing.rest.managed_accounts.routes import router as managed_accounts_router
from app.modules.billing.rest.billing_periods.routes import router as billing_periods_router

__all__ = ["investors_router", "managed_accounts_router", "billing_periods_router"]
