-- =============================================================================
-- Seed: Módulo 4 — Accounts & Portfolio
-- Inserta cuentas de ejemplo para el usuario administrador.
-- Idempotente: usa INSERT IGNORE.
-- =============================================================================

-- Cuenta paper en Binance (desarrollo y pruebas)
INSERT IGNORE INTO accounts (user_id, exchange_id, name, mode, base_currency, status, credentials_ref, meta)
SELECT
  u.id,
  e.id,
  'Binance Paper — Demo',
  'paper',
  'USDT',
  'active',
  NULL,
  JSON_OBJECT('note', 'Cuenta de simulación para desarrollo')
FROM users u, exchanges e
WHERE u.email = 'andrescruznovoa@gmail.com'
  AND e.name  = 'Binance';

-- Cuenta paper en Bybit
INSERT IGNORE INTO accounts (user_id, exchange_id, name, mode, base_currency, status, credentials_ref, meta)
SELECT
  u.id,
  e.id,
  'Bybit Paper — Demo',
  'paper',
  'USDT',
  'active',
  NULL,
  JSON_OBJECT('note', 'Cuenta de simulación Bybit')
FROM users u, exchanges e
WHERE u.email = 'andrescruznovoa@gmail.com'
  AND e.name  = 'Bybit';

-- Balance inicial para la cuenta Binance Paper
INSERT IGNORE INTO account_balances (account_id, asset, free, locked)
SELECT
  a.id,
  'USDT',
  10000.000000000000,
  0.000000000000
FROM accounts a
JOIN users u ON a.user_id = u.id
WHERE u.email = 'andrescruznovoa@gmail.com'
  AND a.name  = 'Binance Paper — Demo';

INSERT IGNORE INTO account_balances (account_id, asset, free, locked)
SELECT
  a.id,
  'BTC',
  0.250000000000,
  0.000000000000
FROM accounts a
JOIN users u ON a.user_id = u.id
WHERE u.email = 'andrescruznovoa@gmail.com'
  AND a.name  = 'Binance Paper — Demo';

-- Balance inicial para la cuenta Bybit Paper
INSERT IGNORE INTO account_balances (account_id, asset, free, locked)
SELECT
  a.id,
  'USDT',
  5000.000000000000,
  0.000000000000
FROM accounts a
JOIN users u ON a.user_id = u.id
WHERE u.email = 'andrescruznovoa@gmail.com'
  AND a.name  = 'Bybit Paper — Demo';

-- Verificación
SELECT
  a.id,
  a.name,
  a.mode,
  a.base_currency,
  a.status,
  e.name AS exchange
FROM accounts a
JOIN exchanges e ON a.exchange_id = e.id
JOIN users u ON a.user_id = u.id
WHERE u.email = 'andrescruznovoa@gmail.com';

SELECT ab.asset, ab.free, ab.locked, a.name AS cuenta
FROM account_balances ab
JOIN accounts a ON ab.account_id = a.id
JOIN users u ON a.user_id = u.id
WHERE u.email = 'andrescruznovoa@gmail.com'
ORDER BY a.id, ab.asset;
