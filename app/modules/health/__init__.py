# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/health/__init__.py
#
# Módulo de health check y status del sistema.
# ======================================================================

from .rest import health_router

__all__ = ["health_router"]
