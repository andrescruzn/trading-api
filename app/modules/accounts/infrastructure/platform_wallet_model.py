# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/platform_wallet_model.py
#
# Modelos ORM de la billetera de la plataforma (fondo común):
# - `platform_wallet`: una sola fila (id = 1) con la cuenta de exchange que
#   guarda el dinero de todos.
# - `wallet_snapshots`: fotos del saldo de esa cuenta valorado en la
#   moneda base, con el desglose por activo en JSON.
# ======================================================================

from __future__ import annotations

from sqlalchemy import (
    DECIMAL,
    JSON,
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import MYSQL_TABLE_OPTIONS, Base


class PlatformWalletModel(Base):
    """Billetera única de la plataforma (la fila id = 1)."""

    __tablename__ = "platform_wallet"
    __table_args__ = (
        UniqueConstraint("account_id", name="uq_platform_wallet_account"),
        CheckConstraint("`id` = 1", name="chk_platform_wallet_single_row"),
        CheckConstraint("`base_asset` <> ''", name="chk_platform_wallet_base_asset"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=False, comment="Siempre 1: hay una sola billetera")
    account_id = Column(
        BigInteger,
        ForeignKey("accounts.id", name="fk_platform_wallet_account"),
        nullable=False,
        comment="Cuenta de exchange que guarda el dinero del fondo",
    )
    base_asset = Column(
        String(16),
        nullable=False,
        server_default=text("'USDT'"),
        comment="Moneda en que se valora la billetera",
    )
    last_synced_at = Column(TIMESTAMP(fsp=6), nullable=True, comment="Última sincronización exitosa")
    last_sync_error = Column(
        String(64), nullable=True, comment="Código del último fallo; NULL si la última salió bien"
    )
    updated_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_platform_wallet_updated_by", ondelete="SET NULL"),
        nullable=True,
    )
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


class WalletSnapshotModel(Base):
    """Foto del saldo de la billetera, valorada en la moneda base."""

    __tablename__ = "wallet_snapshots"
    __table_args__ = (
        Index("idx_wallet_snapshots_account_ts", "account_id", "ts"),
        CheckConstraint(
            "`source` IN ('exchange', 'manual')", name="chk_wallet_snapshots_source"
        ),
        CheckConstraint(
            "`total_value` >= 0 AND `free_value` >= 0 AND `locked_value` >= 0",
            name="chk_wallet_snapshots_values",
        ),
        CheckConstraint("json_valid(`assets`)", name="chk_wallet_snapshots_assets_json"),
        CheckConstraint(
            "json_valid(`missing_prices`)", name="chk_wallet_snapshots_missing_json"
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(
        BigInteger,
        ForeignKey("accounts.id", name="fk_wallet_snapshots_account", ondelete="CASCADE"),
        nullable=False,
    )
    base_asset = Column(String(16), nullable=False)
    total_value = Column(DECIMAL(30, 12), nullable=False, comment="Libre + en órdenes, en base_asset")
    free_value = Column(DECIMAL(30, 12), nullable=False)
    locked_value = Column(DECIMAL(30, 12), nullable=False, comment="En órdenes abiertas")
    source = Column(String(16), nullable=False, comment="exchange | manual")
    assets = Column(JSON, nullable=False, comment="[{asset, free, locked, price, value}]")
    missing_prices = Column(JSON, nullable=False, comment="Activos sin precio: no suman al total")
    ts = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
