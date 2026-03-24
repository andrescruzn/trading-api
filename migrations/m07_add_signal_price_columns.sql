-- ======================================================================
-- Migración M07: Agregar columnas de precio a la tabla `signals`
--
-- Motivo: El Módulo 7 (Bots & Signals) requiere persistir los precios
-- calculados por el Agente (entry, SL, TP, position_size, R/R) y el
-- estado de aprobación de cada señal directamente en la tabla.
--
-- Todas las columnas son NULL para no romper registros existentes.
-- ======================================================================

ALTER TABLE `signals`
    ADD COLUMN `entry_price`   DECIMAL(30,12) NULL DEFAULT NULL COMMENT 'Precio de entrada sugerido por el agente'          AFTER `action`,
    ADD COLUMN `stop_loss`     DECIMAL(30,12) NULL DEFAULT NULL COMMENT 'Nivel de stop loss calculado'                      AFTER `entry_price`,
    ADD COLUMN `take_profit`   DECIMAL(30,12) NULL DEFAULT NULL COMMENT 'Nivel de take profit calculado'                    AFTER `stop_loss`,
    ADD COLUMN `position_size` DECIMAL(30,12) NULL DEFAULT NULL COMMENT 'Tamaño de posición: capital × risk_pct / |entry-SL|' AFTER `take_profit`,
    ADD COLUMN `rr_ratio`      DECIMAL(10,4)  NULL DEFAULT NULL COMMENT 'Ratio Riesgo/Recompensa (TP-entry)/(entry-SL)'     AFTER `position_size`,
    ADD COLUMN `approved`      TINYINT(1)     NOT NULL DEFAULT 1 COMMENT '1=aprobada por todos los filtros, 0=rechazada'    AFTER `rr_ratio`;

-- Verificación
SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'trading_ai'
  AND TABLE_NAME   = 'signals'
ORDER BY ORDINAL_POSITION;
