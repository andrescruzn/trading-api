# -*- coding: utf-8 -*-

from .strategies.routes import router as strategies_router
from .datasets.routes import router as datasets_router

__all__ = [
    "strategies_router",
    "datasets_router",
]
