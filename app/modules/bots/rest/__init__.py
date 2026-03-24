# -*- coding: utf-8 -*-
from app.modules.bots.rest.bots.routes import router as bots_router
from app.modules.bots.rest.signals.routes import router as signals_router

__all__ = ["bots_router", "signals_router"]
