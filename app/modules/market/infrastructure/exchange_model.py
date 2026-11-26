# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/exchange_model.py
#
# Modelo SQLAlchemy para la tabla `exchanges`.
# ======================================================================

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, String, UniqueConstraint, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class ExchangeModel(Base):
    """Modelo SQLAlchemy para la tabla `exchanges`."""

    __tablename__ = "exchanges"
    __table_args__ = (
        UniqueConstraint("name", name="uq_exchanges_name"),
        CheckConstraint(
            "`type` IN ('crypto_exchange', 'broker', 'data_vendor')",
            name="chk_exchanges_type",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    type = Column(String(32), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("'1'"))
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
