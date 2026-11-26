# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/bot_model.py
#
# Modelo SQLAlchemy para la tabla `bots`.
#
# NOTA: el índice de `timeframe_id` lo crea MySQL solo, con el nombre de su
# FK (`fk_bots_timeframe`): no se declara.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    JSON,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class BotModel(Base):
    """Modelo SQLAlchemy para la tabla `bots`."""

    __tablename__ = "bots"
    __table_args__ = (
        Index("idx_bots_status", "status"),
        Index("idx_bots_strategy", "strategy_id"),
        Index("idx_bots_symbol", "symbol_id"),
        Index("idx_bots_account", "account_id"),
        Index("idx_bots_feature_set", "feature_set_id"),
        CheckConstraint("`mode` IN ('paper', 'live')", name="chk_bots_mode"),
        CheckConstraint("json_valid(`risk_params`)", name="chk_bots_risk_params_json"),
        CheckConstraint(
            "`status` IN ('running', 'stopped', 'paused', 'error')",
            name="chk_bots_status",
        ),
        CheckConstraint(
            "`execution_mode` IN ('manual', 'approval', 'auto')",
            name="chk_bots_execution_mode",
        ),
        CheckConstraint(
            "`approval_ttl_minutes` IS NULL OR `approval_ttl_minutes` BETWEEN 1 AND 1440",
            name="chk_bots_approval_ttl",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(
        String(80),
        nullable=False,
        comment="Nombre visible del agente (en la UI los bots se llaman agentes)",
    )
    strategy_id = Column(
        BigInteger,
        ForeignKey("strategies.id", name="fk_bots_strategy"),
        nullable=False,
    )
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id", name="fk_bots_symbol"),
        nullable=False,
    )
    timeframe_id = Column(
        SmallInteger,
        ForeignKey("timeframes.id", name="fk_bots_timeframe"),
        nullable=False,
    )
    mode = Column(String(8), nullable=False)
    execution_mode = Column(
        String(16),
        nullable=False,
        server_default=text("'manual'"),
        comment="manual | approval (aprobación humana) | auto (ejecución automática)",
    )
    approval_ttl_minutes = Column(
        Integer,
        nullable=True,
        comment="Minutos para aprobar una señal antes de que caduque (NULL = valor global)",
    )
    share_signals = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        comment="1 = otros usuarios pueden suscribirse a sus señales (Telegram)",
    )
    status = Column(String(16), nullable=False, server_default=text("'stopped'"))
    risk_params = Column(JSON, nullable=False)
    started_at = Column(TIMESTAMP(fsp=6), nullable=True)
    stopped_at = Column(TIMESTAMP(fsp=6), nullable=True)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    account_id = Column(
        BigInteger,
        ForeignKey("accounts.id", name="fk_bots_account"),
        nullable=True,
    )
    feature_set_id = Column(
        BigInteger,
        ForeignKey("feature_sets.id", name="fk_bots_feature_set"),
        nullable=True,
        comment="Feature set de indicadores técnicos que usa este bot",
    )
