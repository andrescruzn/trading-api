-- =============================================================================
-- Seed: Módulo 5 — Strategies
-- Inserta estrategias de ejemplo para desarrollo y pruebas.
-- Idempotente: usa INSERT IGNORE (UNIQUE KEY en name+version).
-- =============================================================================

INSERT IGNORE INTO strategies (name, version, description, parameters) VALUES

-- ─── Trend Following ────────────────────────────────────────────────────────

('EMA Trend Follower', '1.0.0',
 'Sigue tendencias alcistas usando cruce de EMAs y confirmación de régimen.',
 JSON_OBJECT(
   'strategy_type',   'trend_following',
   'regime_required', 'trend_up',
   'timeframe_code',  '1h',
   'risk_pct',        0.01,
   'rules', JSON_ARRAY(
     JSON_OBJECT('indicator', 'ema_20',  'operator', 'gt', 'value', 'ema_50'),
     JSON_OBJECT('indicator', 'ema_50',  'operator', 'gt', 'value', 'ema_200'),
     JSON_OBJECT('indicator', 'rsi_14',  'operator', 'gt', 'value', 50),
     JSON_OBJECT('indicator', 'macd',    'operator', 'gt', 'value', 0)
   )
 )
),

('EMA Trend Follower', '2.0.0',
 'Versión mejorada: añade filtro ATR para evitar rangos de baja volatilidad.',
 JSON_OBJECT(
   'strategy_type',   'trend_following',
   'regime_required', 'trend_up',
   'timeframe_code',  '4h',
   'risk_pct',        0.01,
   'rules', JSON_ARRAY(
     JSON_OBJECT('indicator', 'ema_20',  'operator', 'gt', 'value', 'ema_50'),
     JSON_OBJECT('indicator', 'ema_50',  'operator', 'gt', 'value', 'ema_200'),
     JSON_OBJECT('indicator', 'rsi_14',  'operator', 'gt', 'value', 55),
     JSON_OBJECT('indicator', 'atr_14',  'operator', 'gt', 'value', 0.005),
     JSON_OBJECT('indicator', 'vol_rel', 'operator', 'gt', 'value', 1.2)
   )
 )
),

('Bearish EMA Follower', '1.0.0',
 'Estrategia bajista: opera en tendencias descendentes con confirmación de EMAs.',
 JSON_OBJECT(
   'strategy_type',   'trend_following',
   'regime_required', 'trend_down',
   'timeframe_code',  '1h',
   'risk_pct',        0.01,
   'rules', JSON_ARRAY(
     JSON_OBJECT('indicator', 'ema_20',  'operator', 'lt', 'value', 'ema_50'),
     JSON_OBJECT('indicator', 'ema_50',  'operator', 'lt', 'value', 'ema_200'),
     JSON_OBJECT('indicator', 'rsi_14',  'operator', 'lt', 'value', 45),
     JSON_OBJECT('indicator', 'macd',    'operator', 'lt', 'value', 0)
   )
 )
),

-- ─── Mean Reversion ─────────────────────────────────────────────────────────

('RSI Mean Reversion', '1.0.0',
 'Compra cuando el precio está sobrevendido en mercados laterales (RSI < 30).',
 JSON_OBJECT(
   'strategy_type',   'mean_reversion',
   'regime_required', 'sideways',
   'timeframe_code',  '15m',
   'risk_pct',        0.005,
   'rules', JSON_ARRAY(
     JSON_OBJECT('indicator', 'rsi_14',   'operator', 'lt', 'value', 30),
     JSON_OBJECT('indicator', 'bb_lower', 'operator', 'gt', 'value', 0),
     JSON_OBJECT('indicator', 'vol_rel',  'operator', 'lt', 'value', 1.5)
   )
 )
),

('Bollinger Band Reversion', '1.0.0',
 'Opera rebotes en las bandas de Bollinger durante mercados en rango lateral.',
 JSON_OBJECT(
   'strategy_type',   'mean_reversion',
   'regime_required', 'sideways',
   'timeframe_code',  '1h',
   'risk_pct',        0.008,
   'rules', JSON_ARRAY(
     JSON_OBJECT('indicator', 'rsi_14',  'operator', 'lt', 'value', 35),
     JSON_OBJECT('indicator', 'rsi_14',  'operator', 'gt', 'value', 20),
     JSON_OBJECT('indicator', 'macd',    'operator', 'gt', 'value', -0.001),
     JSON_OBJECT('indicator', 'vol_rel', 'operator', 'lt', 'value', 2.0)
   )
 )
),

-- ─── Sin restricción de régimen ─────────────────────────────────────────────

('MACD Crossover', '1.0.0',
 'Estrategia universal basada en cruce del MACD. Sin restricción de régimen.',
 JSON_OBJECT(
   'strategy_type',   'trend_following',
   'regime_required', NULL,
   'timeframe_code',  '4h',
   'risk_pct',        0.01,
   'rules', JSON_ARRAY(
     JSON_OBJECT('indicator', 'macd',      'operator', 'gt', 'value', 0),
     JSON_OBJECT('indicator', 'macd_hist', 'operator', 'gt', 'value', 0),
     JSON_OBJECT('indicator', 'rsi_14',    'operator', 'gt', 'value', 45),
     JSON_OBJECT('indicator', 'rsi_14',    'operator', 'lt', 'value', 70)
   )
 )
);

-- Verificación
SELECT
  id,
  name,
  version,
  JSON_UNQUOTE(JSON_EXTRACT(parameters, '$.strategy_type'))   AS tipo,
  JSON_UNQUOTE(JSON_EXTRACT(parameters, '$.regime_required')) AS regimen,
  JSON_UNQUOTE(JSON_EXTRACT(parameters, '$.timeframe_code'))  AS tf,
  JSON_LENGTH(JSON_EXTRACT(parameters, '$.rules'))            AS num_reglas
FROM strategies
ORDER BY id;
