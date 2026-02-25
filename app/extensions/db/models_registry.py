# -*- coding: utf-8 -*-

# ======================================================================
# app/extensions/db/models_registry.py
#
# PROPÓSITO:
# - Importar modelos ORM para que queden registrados en Base.metadata.
#
# POR QUÉ EXISTE:
# - SQLAlchemy solo conoce tablas referenciadas por ForeignKeys si sus
#   modelos fueron importados en runtime.
# - Evita errores como:
#   NoReferencedTableError: users.role_id -> roles.id
#
# NOTA:
# - Aquí NO hay lógica.
# - Solo imports por side-effect controlados.
# ======================================================================

# --------------------------------------------------------------
# Users module models
# --------------------------------------------------------------
from app.modules.users.infrastructure.user_model import UserModel  # noqa: F401
from app.modules.users.infrastructure.role_model import RoleModel  # noqa: F401

# --------------------------------------------------------------
# Market module models
# --------------------------------------------------------------
from app.modules.market.infrastructure.exchange_model import ExchangeModel  # noqa: F401
from app.modules.market.infrastructure.symbol_model import SymbolModel  # noqa: F401
from app.modules.market.infrastructure.timeframe_model import TimeframeModel  # noqa: F401
from app.modules.market.infrastructure.candle_model import CandleModel  # noqa: F401