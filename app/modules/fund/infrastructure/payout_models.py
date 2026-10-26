# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/infrastructure/payout_models.py
#
# Modelos ORM de retiros y comisiones del fondo común (F5):
# - `fee_schedules`: versiones de la tabla de tramos de comisión.
# - `commission_share_versions`: versiones del % de cada propietario.
# - `redemption_requests`: salidas de un agente en cola.
# - `settlement_redemptions`: lo que salió en cada liquidación, con la
#   comisión tramo por tramo.
# - `commission_credits`: la parte de cada comisión de cada propietario.
# - `payout_methods`: medios de pago (banco / Nequi), datos cifrados.
# - `withdrawal_requests`: retiros a banco / Nequi.
# - `withdrawal_receipts`: comprobante del pago de un retiro (F6).
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
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import MEDIUMBLOB, TIMESTAMP, TINYINT

from app.extensions.db import MYSQL_TABLE_OPTIONS, Base


def _created_at() -> Column:
    return Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )


class FeeScheduleModel(Base):
    """Versión de la tabla de tramos de comisión (la vigente es la más nueva)."""

    __tablename__ = "fee_schedules"
    __table_args__ = (
        CheckConstraint("json_valid(`tiers`)", name="chk_fee_schedules_tiers_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tiers = Column(JSON, nullable=False, comment="[{from_return, rate}] en fracción (0.5 = 50 %)")
    note = Column(String(500), nullable=True)
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_fee_schedules_created_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = _created_at()


class CommissionShareVersionModel(Base):
    """Versión del reparto de la comisión entre propietarios (suma 100 %)."""

    __tablename__ = "commission_share_versions"
    __table_args__ = (
        CheckConstraint("json_valid(`shares`)", name="chk_commission_share_versions_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shares = Column(JSON, nullable=False, comment="[{user_id, pct}] en fracción; suman 1")
    note = Column(String(500), nullable=True)
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_commission_share_versions_created_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = _created_at()


class RedemptionRequestModel(Base):
    """Salida de un agente en cola hasta la próxima liquidación."""

    __tablename__ = "redemption_requests"
    __table_args__ = (
        Index("idx_redemption_requests_pool_status", "pool_id", "status"),
        Index("idx_redemption_requests_user_status", "user_id", "status"),
        CheckConstraint(
            "`status` IN ('queued', 'applied', 'canceled')", name="chk_redemption_requests_status"
        ),
        CheckConstraint(
            "`amount` IS NULL OR `amount` > 0", name="chk_redemption_requests_amount"
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pool_id = Column(
        BigInteger,
        ForeignKey("agent_pools.id", name="fk_redemption_requests_pool"),
        nullable=False,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_redemption_requests_user"),
        nullable=False,
    )
    amount = Column(DECIMAL(30, 12), nullable=True, comment="USDT a sacar; NULL = todo lo que cumpla la permanencia")
    status = Column(
        String(16), nullable=False, server_default=text("'queued'"),
        comment="queued | applied | canceled",
    )
    note = Column(String(500), nullable=True)
    settlement_id = Column(
        BigInteger,
        ForeignKey("agent_settlements.id", name="fk_redemption_requests_settlement"),
        nullable=True,
    )
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_redemption_requests_created_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = _created_at()
    resolved_at = Column(TIMESTAMP(fsp=6), nullable=True)


class SettlementRedemptionModel(Base):
    """Lo que salió de un agente para una persona en una liquidación."""

    __tablename__ = "settlement_redemptions"
    __table_args__ = (
        Index("idx_settlement_redemptions_user_created", "user_id", "created_at"),
        CheckConstraint("json_valid(`breakdown`)", name="chk_settlement_redemptions_breakdown"),
        CheckConstraint(
            "`units` > 0 AND `value` >= 0 AND `cost` >= 0 AND `fee` >= 0",
            name="chk_settlement_redemptions_amounts",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    settlement_id = Column(
        BigInteger,
        ForeignKey("agent_settlements.id", name="fk_settlement_redemptions_settlement"),
        nullable=False,
    )
    redemption_request_id = Column(
        BigInteger,
        ForeignKey("redemption_requests.id", name="fk_settlement_redemptions_request"),
        nullable=False,
    )
    pool_id = Column(
        BigInteger,
        ForeignKey("agent_pools.id", name="fk_settlement_redemptions_pool"),
        nullable=False,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_settlement_redemptions_user"),
        nullable=False,
    )
    units = Column(DECIMAL(30, 12), nullable=False)
    value = Column(DECIMAL(30, 12), nullable=False, comment="Unidades × NAV")
    cost = Column(DECIMAL(30, 12), nullable=False, comment="Lo que costaron esas unidades")
    gain = Column(DECIMAL(30, 12), nullable=False, comment="value − cost (puede ser negativa)")
    return_pct = Column(DECIMAL(30, 12), nullable=False, comment="gain / cost en fracción")
    fee = Column(DECIMAL(30, 12), nullable=False, comment="Comisión escalonada")
    net = Column(DECIMAL(30, 12), nullable=False, comment="value − fee: pasa a disponible")
    pending_amount = Column(
        DECIMAL(30, 12), nullable=True, comment="Lo pedido que no salió (permanencia)"
    )
    fee_schedule_id = Column(
        BigInteger,
        ForeignKey("fee_schedules.id", name="fk_settlement_redemptions_fee_schedule"),
        nullable=True,
    )
    commission_version_id = Column(
        BigInteger,
        ForeignKey("commission_share_versions.id", name="fk_settlement_redemptions_commission_version"),
        nullable=True,
    )
    breakdown = Column(JSON, nullable=False, comment="Comisión tramo por tramo")
    created_at = _created_at()


class CommissionCreditModel(Base):
    """La parte de una comisión que recibió un propietario."""

    __tablename__ = "commission_credits"
    __table_args__ = (
        Index("idx_commission_credits_user_created", "user_id", "created_at"),
        CheckConstraint("`amount` > 0", name="chk_commission_credits_amount"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    settlement_redemption_id = Column(
        BigInteger,
        ForeignKey("settlement_redemptions.id", name="fk_commission_credits_redemption"),
        nullable=False,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_commission_credits_user"),
        nullable=False,
    )
    amount = Column(DECIMAL(30, 12), nullable=False)
    created_at = _created_at()


class PayoutMethodModel(Base):
    """A dónde se le envía el dinero a una persona: dirección cripto. Datos cifrados."""

    __tablename__ = "payout_methods"
    __table_args__ = (
        Index("idx_payout_methods_user_active", "user_id", "is_active"),
        # bank / nequi solo en filas viejas (desactivadas); lo nuevo es crypto
        CheckConstraint("`kind` IN ('bank', 'nequi', 'crypto')", name="chk_payout_methods_kind"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_payout_methods_user"),
        nullable=False,
    )
    kind = Column(String(16), nullable=False, comment="crypto (bank | nequi: históricos)")
    label = Column(String(80), nullable=False, comment="Nombre que le pone la persona")
    masked = Column(String(120), nullable=False, comment="Resumen sin datos completos")
    enc_details = Column(Text, nullable=False, comment="Red, dirección y memo cifrados (Fernet)")
    usable_from = Column(
        TIMESTAMP(fsp=6), nullable=False, comment="Antes de esta fecha no se puede usar (seguridad)"
    )
    is_active = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    created_at = _created_at()


class WithdrawalRequestModel(Base):
    """Retiro a una dirección cripto desde el saldo disponible."""

    __tablename__ = "withdrawal_requests"
    __table_args__ = (
        UniqueConstraint("txid", name="uq_withdrawal_requests_txid"),
        Index("idx_withdrawal_requests_status_created", "status", "created_at"),
        Index("idx_withdrawal_requests_user_created", "user_id", "created_at"),
        CheckConstraint(
            "`status` IN ('requested', 'paid', 'rejected', 'canceled')",
            name="chk_withdrawal_requests_status",
        ),
        CheckConstraint("`amount` > 0", name="chk_withdrawal_requests_amount"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_withdrawal_requests_user"),
        nullable=False,
    )
    amount = Column(DECIMAL(30, 12), nullable=False, comment="USDT a retirar")
    payout_method_id = Column(
        BigInteger,
        ForeignKey("payout_methods.id", name="fk_withdrawal_requests_payout_method"),
        nullable=False,
    )
    status = Column(
        String(16), nullable=False, server_default=text("'requested'"),
        comment="requested | paid | rejected | canceled",
    )
    txid = Column(String(128), nullable=True, comment="Hash (o id interno de Binance) del envío")
    network = Column(String(32), nullable=True, comment="Red por la que se envió")
    sent_amount = Column(DECIMAL(30, 12), nullable=True, comment="Lo que recibió el destino")
    network_fee = Column(
        DECIMAL(30, 12), nullable=True, comment="Comisión de red (la paga la persona)"
    )
    exchange_withdrawal_id = Column(String(64), nullable=True, comment="Id del retiro en Binance")
    resolution_note = Column(String(500), nullable=True)
    resolved_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_withdrawal_requests_resolved_by", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at = Column(TIMESTAMP(fsp=6), nullable=True)
    created_at = _created_at()


class WithdrawalReceiptModel(Base):
    """Comprobante del pago de un retiro (PDF / PNG / JPG, máx. 5 MB)."""

    __tablename__ = "withdrawal_receipts"
    __table_args__ = (
        UniqueConstraint("withdrawal_request_id", name="uq_withdrawal_receipts_request"),
        CheckConstraint(
            "`content_type` IN ('application/pdf', 'image/png', 'image/jpeg')",
            name="chk_withdrawal_receipts_type",
        ),
        CheckConstraint(
            "`size_bytes` > 0 AND `size_bytes` <= 5242880", name="chk_withdrawal_receipts_size"
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    withdrawal_request_id = Column(
        BigInteger,
        ForeignKey("withdrawal_requests.id", name="fk_withdrawal_receipts_request"),
        nullable=False,
    )
    filename = Column(String(200), nullable=False)
    content_type = Column(String(64), nullable=False, comment="application/pdf | image/png | image/jpeg")
    size_bytes = Column(Integer, nullable=False)
    content = Column(MEDIUMBLOB, nullable=False, comment="El archivo (tipo validado por su contenido)")
    uploaded_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_withdrawal_receipts_uploaded_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = _created_at()
