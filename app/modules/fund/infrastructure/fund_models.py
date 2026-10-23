# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/infrastructure/fund_models.py
#
# Modelos ORM del fondo común (F3):
# - `fund_settings`: una sola fila (id = 1) con los ajustes del fondo.
# - `ledger_entries`: libro mayor append-only por persona.
# - `deposit_requests`: solicitudes de depósito verificadas contra el exchange.
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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import MYSQL_TABLE_OPTIONS, Base


class FundSettingsModel(Base):
    """Ajustes del fondo común (la fila id = 1)."""

    __tablename__ = "fund_settings"
    __table_args__ = (
        CheckConstraint("`id` = 1", name="chk_fund_settings_single_row"),
        CheckConstraint(
            "`min_hold_days` BETWEEN 0 AND 365", name="chk_fund_settings_min_hold_days"
        ),
        CheckConstraint(
            "`deposit_auto_confirm_max` >= 0", name="chk_fund_settings_auto_confirm_max"
        ),
        CheckConstraint(
            "`deposit_request_ttl_hours` BETWEEN 1 AND 720",
            name="chk_fund_settings_request_ttl",
        ),
        CheckConstraint(
            "json_valid(`deposit_networks`)", name="chk_fund_settings_networks_json"
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=False, comment="Siempre 1: una sola fila")
    min_hold_days = Column(
        Integer,
        nullable=False,
        server_default=text("'30'"),
        comment="Días mínimos que el dinero debe estar en un agente antes de poder retirarlo",
    )
    deposit_auto_confirm_max = Column(
        DECIMAL(30, 12),
        nullable=False,
        server_default=text("'1000.000000000000'"),
        comment="Hasta este monto un depósito verificado se confirma solo; más, lo revisa un super admin",
    )
    deposit_request_ttl_hours = Column(
        Integer,
        nullable=False,
        server_default=text("'72'"),
        comment="Horas que una solicitud espera a que el txid aparezca en el exchange",
    )
    deposit_networks = Column(
        JSON, nullable=False, comment="[{network, name, address, tag}] redes aceptadas para depositar"
    )
    updated_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_fund_settings_updated_by", ondelete="SET NULL"),
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


class LedgerEntryModel(Base):
    """Asiento del libro mayor del fondo (nunca se edita ni se borra)."""

    __tablename__ = "ledger_entries"
    __table_args__ = (
        Index("idx_ledger_entries_user_created", "user_id", "created_at"),
        # La misma referencia (p. ej. una solicitud de depósito) no se asienta dos veces
        UniqueConstraint("entry_type", "ref_type", "ref_id", name="uq_ledger_entries_ref"),
        CheckConstraint(
            "`entry_type` IN ('deposit', 'refund')", name="chk_ledger_entries_entry_type"
        ),
        CheckConstraint(
            "`bucket` IN ('pending', 'available')", name="chk_ledger_entries_bucket"
        ),
        CheckConstraint("`amount` <> 0", name="chk_ledger_entries_amount"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_ledger_entries_user"),
        nullable=False,
        comment="Dueño del saldo (propietario, socio o inversor)",
    )
    entry_type = Column(String(32), nullable=False, comment="deposit | refund (más tipos en F4/F5)")
    bucket = Column(
        String(16),
        nullable=False,
        comment="pending = pendiente de asignar (no se retira) | available = disponible",
    )
    amount = Column(DECIMAL(30, 12), nullable=False, comment="Con signo: + entra, − sale")
    asset = Column(String(16), nullable=False, comment="Moneda del asiento (USDT)")
    ref_type = Column(String(32), nullable=True, comment="Qué originó el asiento (deposit_request…)")
    ref_id = Column(BigInteger, nullable=True)
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_ledger_entries_bot"),
        nullable=True,
        comment="Agente relacionado (desde la F4)",
    )
    description = Column(String(500), nullable=True)
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_ledger_entries_created_by", ondelete="SET NULL"),
        nullable=True,
        comment="NULL = lo registró el sistema",
    )
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )


class DepositRequestModel(Base):
    """Solicitud de depósito de un participante, verificada contra el exchange."""

    __tablename__ = "deposit_requests"
    __table_args__ = (
        UniqueConstraint("txid", name="uq_deposit_requests_txid"),
        Index("idx_deposit_requests_status_created", "status", "created_at"),
        Index("idx_deposit_requests_user_created", "user_id", "created_at"),
        CheckConstraint(
            "`status` IN ('pending', 'review', 'confirmed', 'rejected', 'expired', 'canceled')",
            name="chk_deposit_requests_status",
        ),
        CheckConstraint(
            "`review_reason` IS NULL OR `review_reason` IN "
            "('amount_mismatch', 'over_threshold', 'exchange_failed', 'wrong_asset')",
            name="chk_deposit_requests_review_reason",
        ),
        CheckConstraint("`declared_amount` > 0", name="chk_deposit_requests_declared_amount"),
        CheckConstraint(
            "`credited_amount` IS NULL OR `credited_amount` >= 0",
            name="chk_deposit_requests_credited_amount",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_deposit_requests_user"),
        nullable=False,
    )
    asset = Column(String(16), nullable=False)
    network = Column(String(32), nullable=False, comment="Red por la que se envió (p. ej. TRC20)")
    txid = Column(String(128), nullable=False, comment="Hash de la transacción (normalizado)")
    declared_amount = Column(DECIMAL(30, 12), nullable=False, comment="Lo que la persona dice que envió")
    credited_amount = Column(
        DECIMAL(30, 12), nullable=True, comment="Lo que reporta el exchange (lo que se acredita)"
    )
    address_from = Column(String(255), nullable=True, comment="Dirección de origen según el exchange")
    exchange_deposit_id = Column(String(128), nullable=True)
    exchange_status = Column(String(16), nullable=True, comment="pending | ok | failed | canceled")
    status = Column(
        String(16), nullable=False, server_default=text("'pending'"),
        comment="pending | review | confirmed | rejected | expired | canceled",
    )
    review_reason = Column(String(32), nullable=True)
    resolved_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_deposit_requests_resolved_by", ondelete="SET NULL"),
        nullable=True,
        comment="Super admin que confirmó o rechazó; NULL en una confirmación automática",
    )
    resolved_at = Column(TIMESTAMP(fsp=6), nullable=True)
    resolution_note = Column(String(500), nullable=True)
    expires_at = Column(TIMESTAMP(fsp=6), nullable=False, comment="Vence si el txid no aparece antes")
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
