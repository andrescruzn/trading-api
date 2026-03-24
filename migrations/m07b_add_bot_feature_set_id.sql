-- ======================================================================
-- Migración M07b: Agregar feature_set_id a la tabla `bots`
--
-- Motivo: Cada bot debe poder usar su propio feature set de indicadores
-- técnicos al momento de generar señales via el Agente (M6).
-- ======================================================================

ALTER TABLE `bots`
    ADD COLUMN `feature_set_id` BIGINT NULL DEFAULT NULL
        COMMENT 'Feature set de indicadores técnicos que usa este bot'
        AFTER `account_id`,
    ADD CONSTRAINT `fk_bots_feature_set`
        FOREIGN KEY (`feature_set_id`) REFERENCES `feature_sets` (`id`);

-- Verificación
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'trading_ai' AND TABLE_NAME = 'bots'
ORDER BY ORDINAL_POSITION;
