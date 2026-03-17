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

# --------------------------------------------------------------
# Features module models
# --------------------------------------------------------------
from app.modules.features.infrastructure.feature_set_model import FeatureSetModel  # noqa: F401
from app.modules.features.infrastructure.candle_feature_model import CandleFeatureModel  # noqa: F401

# --------------------------------------------------------------
# Accounts module models
# --------------------------------------------------------------
from app.modules.accounts.infrastructure.account_model import AccountModel  # noqa: F401
from app.modules.accounts.infrastructure.account_balance_model import AccountBalanceModel  # noqa: F401

# --------------------------------------------------------------
# Strategies module models
# --------------------------------------------------------------
from app.modules.strategies.infrastructure.strategy_model import StrategyModel  # noqa: F401
from app.modules.strategies.infrastructure.dataset_model import DatasetModel  # noqa: F401

# --------------------------------------------------------------
# Agent module models
# --------------------------------------------------------------
from app.modules.agent.infrastructure.ml_model_model import MLModelORM  # noqa: F401
from app.modules.agent.infrastructure.model_run_model import ModelRunORM  # noqa: F401