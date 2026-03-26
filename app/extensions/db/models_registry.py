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

# --------------------------------------------------------------
# Bots module models
# --------------------------------------------------------------
from app.modules.bots.infrastructure.bot_model import BotModel  # noqa: F401
from app.modules.bots.infrastructure.signal_model import SignalModel  # noqa: F401

# --------------------------------------------------------------
# Orders module models
# --------------------------------------------------------------
from app.modules.orders.infrastructure.order_model import OrderModel  # noqa: F401
from app.modules.orders.infrastructure.fill_model import FillModel  # noqa: F401
from app.modules.orders.infrastructure.position_model import PositionModel  # noqa: F401

# --------------------------------------------------------------
# Alerts module models
# --------------------------------------------------------------
from app.modules.alerts.infrastructure.alert_rule_model import AlertRuleModel  # noqa: F401
from app.modules.alerts.infrastructure.alert_event_model import AlertEventModel  # noqa: F401