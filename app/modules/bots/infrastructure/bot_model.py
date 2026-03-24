# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/bot_model.py
#
# Modelo SQLAlchemy para la tabla `bots`.
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, JSON, SmallInteger, String, TIMESTAMP, text

from app.extensions.db import Base


class BotModel(Base):
    """Modelo SQLAlchemy para la tabla `bots`."""

    __tablename__ = "bots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    strategy_id = Column(
        BigInteger,
        ForeignKey("strategies.id"),
        nullable=False,
        index=True,
    )
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id"),
        nullable=False,
        index=True,
    )
    timeframe_id = Column(
        SmallInteger,
        ForeignKey("timeframes.id"),
        nullable=False,
        index=True,
    )
    account_id = Column(
        BigInteger,
        ForeignKey("accounts.id"),
        nullable=True,
        index=True,
    )
    feature_set_id = Column(
        BigInteger,
        ForeignKey("feature_sets.id"),
        nullable=True,
        index=True,
    )
    mode = Column(String(8), nullable=False)
    status = Column(String(16), nullable=False, server_default=text("'stopped'"))
    risk_params = Column(JSON, nullable=False)
    started_at = Column(TIMESTAMP(6), nullable=True)
    stopped_at = Column(TIMESTAMP(6), nullable=True)
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
