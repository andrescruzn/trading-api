# Módulo 2 — Market Data (Datos de Mercado) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

**En palabras simples:** Es la bodega de datos. Guarda toda la información de los precios de los activos financieros a lo largo del tiempo.

**Qué hace:**
- Registra los **exchanges** (plataformas de trading) como Binance, Bybit, Kraken, etc.
- Registra los **símbolos** (pares de trading) como BTC/USDT, ETH/USDT, EUR/USD, XAU/USD, etc.
- Registra los **timeframes** (marcos de tiempo) como 1 minuto, 5 minutos, 1 hora, 1 día, etc.
- Almacena **velas OHLCV**: cada vela es un resumen del precio en un período de tiempo (precio de apertura, precio más alto, precio más bajo, precio de cierre y volumen negociado)

**Páginas:**
- `/market/symbols` — Lista de todos los símbolos disponibles (para todos los usuarios)
- `/market/candles` — Ver las velas/precios de un símbolo (para todos los usuarios)
- `/admin/exchanges` — Gestionar exchanges (solo Administrador)
- `/admin/symbols` — Gestionar símbolos (solo Administrador)
- `/admin/timeframes` — Gestionar timeframes (solo Administrador)
- `/admin/candles/ingest` — Cargar velas/precios históricos (solo Administrador)
