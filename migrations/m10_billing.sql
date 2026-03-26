-- ======================================================================
-- m10_billing.sql
--
-- Módulo 10: Billing & Managed Accounts
--
-- Tablas nuevas:
--   1. investors          → extensión de users con datos de negocio del inversor
--   2. managed_accounts   → cuenta de trading gestionada por un bot para un inversor
--   3. billing_periods    → período de facturación con cálculo de PnL y fee
--   4. fee_transactions   → registro auditable de cada cobro de performance fee
--
-- IMPORTANTE: Ejecutar DESPUÉS de que existan: users, accounts, bots
-- ======================================================================

-- ----------------------------------------------------------------------
-- 1. investors
--
-- Un inversor ES un usuario con role_id=3 (investor).
-- Esta tabla extiende users con los datos de negocio propios del inversor:
-- la tasa de performance fee y si está activo como inversor.
-- Relación 1:1 con users (UNIQUE user_id).
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `investors` (
  `id`         BIGINT       NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT       NOT NULL,
  `fee_pct`    DECIMAL(5,4) NOT NULL DEFAULT '0.2000'
                            COMMENT 'Performance fee ej: 0.2000 = 20%',
  `is_active`  TINYINT(1)   NOT NULL DEFAULT 1,
  `created_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
               ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_investors_user_id` (`user_id`),
  KEY `idx_investors_active` (`is_active`),
  CONSTRAINT `fk_investors_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chk_investors_fee_pct`
    CHECK (`fee_pct` >= 0 AND `fee_pct` <= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ----------------------------------------------------------------------
-- 2. managed_accounts
--
-- Une a un inversor con la cuenta de trading que el bot opera.
-- Guarda el High-Water Mark (HWM): el máximo de equity histórico alcanzado.
-- La performance fee solo se cobra sobre ganancia POR ENCIMA del HWM.
--
-- period_type define la frecuencia de facturación:
--   daily | weekly | monthly
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `managed_accounts` (
  `id`                BIGINT        NOT NULL AUTO_INCREMENT,
  `investor_id`       BIGINT        NOT NULL,
  `account_id`        BIGINT        NOT NULL,
  `bot_id`            BIGINT        NULL,
  `name`              VARCHAR(120)  NOT NULL,
  `initial_capital`   DECIMAL(30,12) NOT NULL DEFAULT '0.000000000000'
                      COMMENT 'Capital inicial aportado por el inversor',
  `high_water_mark`   DECIMAL(30,12) NOT NULL DEFAULT '0.000000000000'
                      COMMENT 'Máximo equity histórico alcanzado (base para HWM fee)',
  `period_type`       VARCHAR(16)   NOT NULL DEFAULT 'monthly'
                      COMMENT 'Frecuencia de facturación: daily | weekly | monthly',
  `is_active`         TINYINT(1)    NOT NULL DEFAULT 1,
  `created_at`        TIMESTAMP(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at`        TIMESTAMP(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                      ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_managed_accounts_investor` (`investor_id`),
  KEY `idx_managed_accounts_account` (`account_id`),
  KEY `idx_managed_accounts_bot` (`bot_id`),
  KEY `idx_managed_accounts_active` (`is_active`),
  CONSTRAINT `fk_managed_accounts_investor`
    FOREIGN KEY (`investor_id`) REFERENCES `investors` (`id`),
  CONSTRAINT `fk_managed_accounts_account`
    FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`),
  CONSTRAINT `fk_managed_accounts_bot`
    FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `chk_managed_accounts_period_type`
    CHECK (`period_type` IN ('daily', 'weekly', 'monthly')),
  CONSTRAINT `chk_managed_accounts_capital`
    CHECK (`initial_capital` >= 0 AND `high_water_mark` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ----------------------------------------------------------------------
-- 3. billing_periods
--
-- Cada período de facturación asociado a una managed_account.
-- Un período puede estar:
--   open   → en curso, sin fee calculado todavía
--   closed → cerrado, con fee calculado y fee_transaction creada
--
-- Lógica HWM al cierre:
--   gross_pnl = closing_equity - MAX(opening_equity, high_water_mark)
--   Si gross_pnl > 0:
--     fee_amount = gross_pnl * fee_pct
--     net_pnl    = gross_pnl - fee_amount
--     → actualizar managed_accounts.high_water_mark = closing_equity
--   Si gross_pnl <= 0:
--     fee_amount = 0
--     net_pnl    = gross_pnl
--     → HWM no cambia
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `billing_periods` (
  `id`                  BIGINT        NOT NULL AUTO_INCREMENT,
  `managed_account_id`  BIGINT        NOT NULL,
  `start_ts`            TIMESTAMP(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `end_ts`              TIMESTAMP(6)  NULL     DEFAULT NULL,
  `opening_equity`      DECIMAL(30,12) NOT NULL DEFAULT '0.000000000000',
  `closing_equity`      DECIMAL(30,12) NULL     DEFAULT NULL,
  `gross_pnl`           DECIMAL(30,12) NULL     DEFAULT NULL
                        COMMENT 'closing_equity - MAX(opening_equity, HWM)',
  `fee_pct`             DECIMAL(5,4)  NOT NULL DEFAULT '0.0000'
                        COMMENT 'Snapshot del fee_pct al abrir el período',
  `fee_amount`          DECIMAL(30,12) NULL     DEFAULT NULL,
  `net_pnl`             DECIMAL(30,12) NULL     DEFAULT NULL
                        COMMENT 'gross_pnl - fee_amount',
  `status`              VARCHAR(16)   NOT NULL DEFAULT 'open',
  `created_at`          TIMESTAMP(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `closed_at`           TIMESTAMP(6)  NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_billing_periods_managed_account` (`managed_account_id`),
  KEY `idx_billing_periods_status` (`status`),
  KEY `idx_billing_periods_start_ts` (`managed_account_id`, `start_ts`),
  CONSTRAINT `fk_billing_periods_managed_account`
    FOREIGN KEY (`managed_account_id`) REFERENCES `managed_accounts` (`id`),
  CONSTRAINT `chk_billing_periods_status`
    CHECK (`status` IN ('open', 'closed')),
  CONSTRAINT `chk_billing_periods_equity`
    CHECK (`opening_equity` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ----------------------------------------------------------------------
-- 4. fee_transactions
--
-- Registro auditable de cada cobro de performance fee.
-- Un billing_period cerrado con gross_pnl > 0 genera exactamente
-- una fee_transaction.
--
-- status:
--   pending  → fee calculada pero no registrada aún como cobrada
--   charged  → fee efectivamente cobrada / descontada del capital
--   waived   → fee condonada (decisión administrativa)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `fee_transactions` (
  `id`                  BIGINT        NOT NULL AUTO_INCREMENT,
  `billing_period_id`   BIGINT        NOT NULL,
  `managed_account_id`  BIGINT        NOT NULL,
  `amount`              DECIMAL(30,12) NOT NULL DEFAULT '0.000000000000',
  `status`              VARCHAR(16)   NOT NULL DEFAULT 'pending',
  `charged_at`          TIMESTAMP(6)  NULL     DEFAULT NULL,
  `notes`               TEXT          NULL,
  `created_at`          TIMESTAMP(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_fee_transactions_period` (`billing_period_id`)
             COMMENT 'Un período → máximo una fee_transaction',
  KEY `idx_fee_transactions_managed_account` (`managed_account_id`),
  KEY `idx_fee_transactions_status` (`status`),
  CONSTRAINT `fk_fee_transactions_billing_period`
    FOREIGN KEY (`billing_period_id`) REFERENCES `billing_periods` (`id`),
  CONSTRAINT `fk_fee_transactions_managed_account`
    FOREIGN KEY (`managed_account_id`) REFERENCES `managed_accounts` (`id`),
  CONSTRAINT `chk_fee_transactions_status`
    CHECK (`status` IN ('pending', 'charged', 'waived')),
  CONSTRAINT `chk_fee_transactions_amount`
    CHECK (`amount` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
