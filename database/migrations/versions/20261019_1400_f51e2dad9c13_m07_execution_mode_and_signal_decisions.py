"""m07 execution mode and signal decisions

Revision ID: f51e2dad9c13
Revises: 218d50385270
Create Date: 2026-10-19 14:00:00.000000+00:00

MOTIVO (modo de ejecución del agente: manual / con aprobación / automático):
- bots.execution_mode VARCHAR(16) NOT NULL DEFAULT 'manual' + CHECK
  (manual | approval | auto) y bots.approval_ttl_minutes INT NULL + CHECK
  (1–1440). Los agentes existentes quedan en `manual` (comportamiento actual).
- signals: estado de la decisión humana/automática (decision_status +
  CHECK, expires_at, decided_at, decided_by_user_id FK users,
  decision_channel + CHECK, decision_reason) y candle_ts con
  UNIQUE (bot_id, candle_ts): una señal automática por vela y agente
  (las manuales tienen candle_ts NULL y no chocan). Índice
  (decision_status, expires_at) para la cola y la caducidad.
- positions.stop_loss / take_profit DECIMAL(30,12) y signal_id (FK signals):
  protección que vigila el scheduler.
- users.telegram_chat_id BIGINT UNIQUE, telegram_link_hash VARCHAR(64)
  (índice) y telegram_link_expires_at: vínculo del chat de Telegram.
- Escrita a mano para ubicar las columnas junto a su grupo (AFTER) y
  añadir los CHECK en tablas existentes, que autogenerate no detecta.
- El downgrade elimina todo lo anterior (se pierden decisiones, SL/TP y
  vínculos de Telegram).
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'f51e2dad9c13'
down_revision: str | Sequence[str] | None = '218d50385270'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # bots
    # ------------------------------------------------------------------
    op.execute(sa.text(
        "ALTER TABLE bots "
        "ADD COLUMN execution_mode VARCHAR(16) NOT NULL DEFAULT 'manual' "
        "COMMENT 'manual | approval (aprobación humana) | auto (ejecución automática)' AFTER mode, "
        "ADD COLUMN approval_ttl_minutes INT NULL "
        "COMMENT 'Minutos para aprobar una señal antes de que caduque (NULL = valor global)' "
        "AFTER execution_mode, "
        "ADD CONSTRAINT chk_bots_execution_mode "
        "CHECK (`execution_mode` IN ('manual', 'approval', 'auto')), "
        "ADD CONSTRAINT chk_bots_approval_ttl "
        "CHECK (`approval_ttl_minutes` IS NULL OR `approval_ttl_minutes` BETWEEN 1 AND 1440)"
    ))

    # ------------------------------------------------------------------
    # signals
    # ------------------------------------------------------------------
    op.execute(sa.text(
        "ALTER TABLE signals "
        "ADD COLUMN decision_status VARCHAR(16) NOT NULL DEFAULT 'not_required' "
        "COMMENT 'not_required | pending | executing | executed | rejected | expired | failed' "
        "AFTER llm_latency_ms, "
        "ADD COLUMN expires_at TIMESTAMP(6) NULL COMMENT 'Límite para aprobar la señal' "
        "AFTER decision_status, "
        "ADD COLUMN decided_at TIMESTAMP(6) NULL COMMENT 'Cuándo se aprobó o rechazó' "
        "AFTER expires_at, "
        "ADD COLUMN decided_by_user_id BIGINT NULL "
        "COMMENT 'Quién decidió (NULL = ejecución automática)' AFTER decided_at, "
        "ADD COLUMN decision_channel VARCHAR(16) NULL COMMENT 'app | telegram | auto' "
        "AFTER decided_by_user_id, "
        "ADD COLUMN decision_reason VARCHAR(64) NULL COMMENT 'Código del fallo al ejecutar' "
        "AFTER decision_channel, "
        "ADD COLUMN candle_ts TIMESTAMP(6) NULL "
        "COMMENT 'Vela que originó la señal automática (NULL en las manuales)' "
        "AFTER decision_reason, "
        "ADD CONSTRAINT fk_signals_decided_by FOREIGN KEY (decided_by_user_id) REFERENCES users (id), "
        "ADD CONSTRAINT uq_signals_bot_candle UNIQUE (bot_id, candle_ts), "
        "ADD INDEX idx_signals_decision_status (decision_status, expires_at), "
        "ADD CONSTRAINT chk_signals_decision_status CHECK (`decision_status` IN "
        "('not_required', 'pending', 'executing', 'executed', 'rejected', 'expired', 'failed')), "
        "ADD CONSTRAINT chk_signals_decision_channel CHECK (`decision_channel` IS NULL "
        "OR `decision_channel` IN ('app', 'telegram', 'auto'))"
    ))

    # ------------------------------------------------------------------
    # positions
    # ------------------------------------------------------------------
    op.execute(sa.text(
        "ALTER TABLE positions "
        "ADD COLUMN stop_loss DECIMAL(30,12) NULL COMMENT 'Stop loss vigilado por el scheduler' "
        "AFTER realized_pnl, "
        "ADD COLUMN take_profit DECIMAL(30,12) NULL COMMENT 'Take profit vigilado por el scheduler' "
        "AFTER stop_loss, "
        "ADD COLUMN signal_id BIGINT NULL COMMENT 'Señal que abrió la posición' AFTER take_profit, "
        "ADD CONSTRAINT fk_positions_signal FOREIGN KEY (signal_id) REFERENCES signals (id)"
    ))

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.execute(sa.text(
        "ALTER TABLE users "
        "ADD COLUMN telegram_chat_id BIGINT NULL "
        "COMMENT 'Chat privado vinculado con el bot de Telegram' AFTER otp_failed_attempts, "
        "ADD COLUMN telegram_link_hash VARCHAR(64) NULL "
        "COMMENT 'SHA-256 del código de vinculación de un solo uso' AFTER telegram_chat_id, "
        "ADD COLUMN telegram_link_expires_at TIMESTAMP(6) NULL AFTER telegram_link_hash, "
        "ADD CONSTRAINT uq_users_telegram_chat UNIQUE (telegram_chat_id), "
        "ADD INDEX idx_users_telegram_link (telegram_link_hash)"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE users "
        "DROP INDEX idx_users_telegram_link, "
        "DROP INDEX uq_users_telegram_chat, "
        "DROP COLUMN telegram_link_expires_at, "
        "DROP COLUMN telegram_link_hash, "
        "DROP COLUMN telegram_chat_id"
    ))

    op.execute(sa.text("ALTER TABLE positions DROP FOREIGN KEY fk_positions_signal"))
    op.execute(sa.text(
        "ALTER TABLE positions "
        "DROP INDEX fk_positions_signal, "
        "DROP COLUMN signal_id, "
        "DROP COLUMN take_profit, "
        "DROP COLUMN stop_loss"
    ))

    op.execute(sa.text("ALTER TABLE signals DROP FOREIGN KEY fk_signals_decided_by"))
    op.execute(sa.text(
        "ALTER TABLE signals "
        "DROP CHECK chk_signals_decision_channel, "
        "DROP CHECK chk_signals_decision_status, "
        "DROP INDEX idx_signals_decision_status, "
        "DROP INDEX uq_signals_bot_candle, "
        "DROP INDEX fk_signals_decided_by, "
        "DROP COLUMN candle_ts, "
        "DROP COLUMN decision_reason, "
        "DROP COLUMN decision_channel, "
        "DROP COLUMN decided_by_user_id, "
        "DROP COLUMN decided_at, "
        "DROP COLUMN expires_at, "
        "DROP COLUMN decision_status"
    ))

    op.execute(sa.text(
        "ALTER TABLE bots "
        "DROP CHECK chk_bots_approval_ttl, "
        "DROP CHECK chk_bots_execution_mode, "
        "DROP COLUMN approval_ttl_minutes, "
        "DROP COLUMN execution_mode"
    ))
