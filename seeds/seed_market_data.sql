-- ======================================================================
-- seeds/seed_market_data.sql
--
-- Datos iniciales para el Módulo 2 — Market Data.
-- Base de datos: trading_ai
--
-- CÓMO EJECUTAR:
--   mysql -u <user> -p trading_ai < seeds/seed_market_data.sql
--
-- IDEMPOTENTE: usa INSERT IGNORE para no duplicar registros.
-- ======================================================================

USE trading_ai;

-- ======================================================================
-- 1. EXCHANGES
-- ======================================================================

INSERT IGNORE INTO exchanges (name, type, is_active) VALUES
  ('Binance',    'crypto_exchange', 1),
  ('Bybit',      'crypto_exchange', 1),
  ('Kraken',     'crypto_exchange', 1),
  ('Coinbase',   'crypto_exchange', 1),
  ('Bitget',     'crypto_exchange', 1),
  ('OKX',        'crypto_exchange', 1),
  ('TradingView','data_vendor',     1);

-- ======================================================================
-- 2. TIMEFRAMES
-- ======================================================================

INSERT IGNORE INTO timeframes (code, seconds) VALUES
  ('1m',    60),
  ('3m',   180),
  ('5m',   300),
  ('15m',  900),
  ('30m', 1800),
  ('1h',  3600),
  ('2h',  7200),
  ('4h', 14400),
  ('6h', 21600),
  ('8h', 28800),
  ('12h',43200),
  ('1d', 86400),
  ('3d',259200),
  ('1w',604800);

-- ======================================================================
-- 3. SYMBOLS (asociados a Binance)
--    Usamos subquery para no hardcodear IDs.
-- ======================================================================

-- Crypto pairs — Binance
INSERT IGNORE INTO symbols (exchange_id, symbol, base_asset, quote_asset, asset_class, is_active)
SELECT id, 'BTC/USDT',  'BTC',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'ETH/USDT',  'ETH',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'BNB/USDT',  'BNB',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'SOL/USDT',  'SOL',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'XRP/USDT',  'XRP',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'ADA/USDT',  'ADA',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'DOGE/USDT', 'DOGE', 'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'AVAX/USDT', 'AVAX', 'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'LINK/USDT', 'LINK', 'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'DOT/USDT',  'DOT',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'MATIC/USDT','MATIC','USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'UNI/USDT',  'UNI',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'ATOM/USDT', 'ATOM', 'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'LTC/USDT',  'LTC',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance'
UNION ALL
SELECT id, 'BCH/USDT',  'BCH',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Binance';

-- Crypto pairs — Bybit
INSERT IGNORE INTO symbols (exchange_id, symbol, base_asset, quote_asset, asset_class, is_active)
SELECT id, 'BTC/USDT',  'BTC',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Bybit'
UNION ALL
SELECT id, 'ETH/USDT',  'ETH',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Bybit'
UNION ALL
SELECT id, 'SOL/USDT',  'SOL',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Bybit'
UNION ALL
SELECT id, 'XRP/USDT',  'XRP',  'USDT', 'crypto', 1 FROM exchanges WHERE name = 'Bybit';

-- Metales (data vendor TradingView)
INSERT IGNORE INTO symbols (exchange_id, symbol, base_asset, quote_asset, asset_class, is_active)
SELECT id, 'XAU/USD', 'XAU', 'USD', 'metal', 1 FROM exchanges WHERE name = 'TradingView'
UNION ALL
SELECT id, 'XAG/USD', 'XAG', 'USD', 'metal', 1 FROM exchanges WHERE name = 'TradingView';

-- Forex (data vendor TradingView)
INSERT IGNORE INTO symbols (exchange_id, symbol, base_asset, quote_asset, asset_class, is_active)
SELECT id, 'EUR/USD', 'EUR', 'USD', 'forex', 1 FROM exchanges WHERE name = 'TradingView'
UNION ALL
SELECT id, 'GBP/USD', 'GBP', 'USD', 'forex', 1 FROM exchanges WHERE name = 'TradingView'
UNION ALL
SELECT id, 'USD/JPY', 'USD', 'JPY', 'forex', 1 FROM exchanges WHERE name = 'TradingView';

-- ======================================================================
-- Verificar
-- ======================================================================

SELECT 'exchanges' AS tabla, COUNT(*) AS total FROM exchanges
UNION ALL
SELECT 'timeframes', COUNT(*) FROM timeframes
UNION ALL
SELECT 'symbols', COUNT(*) FROM symbols;
