# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/account_model.py
#
# Modelo SQLAlchemy para la tabla `accounts`.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, ForeignKey, Index, JSON, String, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class AccountModel(Base):
    """Modelo SQLAlchemy para la tabla `accounts`."""

    __tablename__ = "accounts"
    __table_args__ = (
        Index("idx_accounts_user", "user_id"),
        Index("idx_accounts_mode", "mode"),
        Index("idx_accounts_exchange", "exchange_id"),
        CheckConstraint("json_valid(`meta`)", name="chk_accounts_meta_json"),
        CheckConstraint("`mode` IN ('paper', 'live')", name="chk_accounts_mode"),
        CheckConstraint("`status` IN ('active', 'suspended')", name="chk_accounts_status"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_accounts_user"),
        nullable=False,
    )
    exchange_id = Column(
        BigInteger,
        ForeignKey("exchanges.id", name="fk_accounts_exchange"),
        nullable=True,
    )
    name = Column(String(120), nullable=False)
    mode = Column(String(8), nullable=False)
    base_currency = Column(String(16), nullable=False, server_default=text("'USD'"))
    status = Column(String(16), nullable=False, server_default=text("'active'"))
    credentials_ref = Column(String(255), nullable=True)
    meta = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )
