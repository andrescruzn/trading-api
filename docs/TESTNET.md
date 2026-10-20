# Prueba del circuito live en testnet

Antes del primer peso real hay que ver el circuito live funcionando contra la **testnet** de cada exchange que se vaya a usar. Hay dos niveles: el script (solo el ejecutor, sin BD) y la prueba completa en la app.

> Las claves de testnet se crean en el sitio de testnet de cada exchange (p. ej. Binance Spot: <https://testnet.binance.vision>). Las de producción no funcionan en la testnet ni al revés.

## 1. Script del ejecutor (5 minutos)

Prueba el `LiveExecutor` real: compra, consulta, stop loss nativo, cancelación de una límite y venta. No usa la BD.

```bash
TESTNET_EXCHANGE=binance \
TESTNET_API_KEY=<clave de testnet> \
TESTNET_API_SECRET=<secreto de testnet> \
TESTNET_SYMBOL=BTC/USDT \
TESTNET_QTY=0.001 \
uv run python -m scripts.testnet_check --yes
```

Debe terminar con "Listo: el circuito live respondió en la testnet." Anota el resultado de cada paso; si el paso 3 dice "SL nativo no disponible", ese exchange queda protegido solo por el scheduler.

## 2. Circuito completo en la app

Configura el `.env` del backend y reinicia la API:

```
LIVE_USE_SANDBOX=true
TRADING_LIVE_ENABLED=true
ORDER_MAX_NOTIONAL=200        # tope bajo mientras se prueba
ORDER_NATIVE_STOP_LOSS=true
```

| # | Paso | Qué comprobar |
|---|---|---|
| 1 | Crear una cuenta **live** con las claves de testnet (Mis cuentas) | Se guarda; las credenciales no se muestran |
| 2 | Crear un agente live con esa cuenta e iniciarlo; en Mercado, "Actualizar datos" | Aparecen velas e indicadores |
| 3 | Orden manual: compra a mercado pequeña con stop loss y take profit | Orden `filled`; en Posiciones, "Protección automática" y "El stop loss está como orden en el exchange"; en Órdenes, una orden stop `sent` |
| 4 | En la testnet, ver la orden stop abierta | Mismo precio y cantidad |
| 5 | Cancelar esa orden stop desde la app | Queda `canceled`; la posición conserva el SL (lo vigila el scheduler) |
| 6 | Orden límite de compra muy por debajo del precio | Queda `sent` (abierta) |
| 7 | Cancelarla desde la app | Queda `canceled`; en la testnet ya no aparece |
| 8 | Vender la posición (orden manual) | Se cancela antes cualquier SL nativo; posición en 0 |
| 9 | Modo **Con aprobación**: esperar una señal BUY y aprobarla | Orden ejecutada y SL nativo colocado |
| 10 | Repetir el paso 3 con niveles cercanos (TP a +1 %, SL a −0,5 %) y esperar a que una vela toque el TP | El scheduler vende por TP y cancela antes el SL nativo |
| 11 | Apagar la API 2 ciclos con una límite abierta que se ejecute en la testnet; encenderla | La reconciliación registra el fill tardío |
| 12 | `TRADING_ENABLED=false` y crear una orden | Rechazada: "El envío de órdenes está detenido…" |

Al terminar, deja `LIVE_USE_SANDBOX=false` y `TRADING_LIVE_ENABLED=false` hasta decidir el paso a producción, y anota en `specs/M08-ORDERS-EXECUTION.md` (Avance → Tests) qué exchange se probó y con qué resultado.
