-- ======================================================================
-- seed_billing.sql
--
-- Módulo 10: Billing & Managed Accounts
--
-- Inserta:
--   1. Rol 'investor' (id=3) en la tabla roles
--
-- Idempotente: usa INSERT IGNORE (no falla si ya existe).
-- ======================================================================

-- ----------------------------------------------------------------------
-- Rol investor
--
-- role_id=3 → investor
-- El inversor solo puede ver su propio dashboard (/investor/dashboard).
-- NO puede acceder a rutas admin ni de usuario regular.
-- ----------------------------------------------------------------------
INSERT IGNORE INTO `roles` (`id`, `code`, `name`, `is_active`, `created_at`)
VALUES (3, 'investor', 'Inversor', 1, NOW(6));

-- Verificación
SELECT id, code, name, is_active FROM roles ORDER BY id;
