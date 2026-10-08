# Rol notificación: directo y accionable

Para lo que el sistema envía hacia afuera: correos (`app/modules/mailer/templates/`), mensajes de Telegram, alertas de escritorio y payloads de webhook con texto (`app/modules/alerts/channels/`). La persona no está mirando la app: el mensaje tiene que entenderse completo en la vista previa del celular.

## Principios

- **Lo importante en la primera línea**: qué pasó y sobre qué. `Señal de compra · BTC/USDT 1h` antes que cualquier saludo.
- **Datos, no adjetivos.** Entrada, stop loss, take profit, R/R, tamaño. Nunca "gran oportunidad".
- **Un llamado a la acción, si existe**: `Revisa la señal en Trading App`. Si no hay nada que hacer, no inventes uno.
- **Severidad honesta**: `Info`, `Advertencia`, `Crítico` según el evento; no subas el tono para llamar la atención.
- **Nada sensible**: sin claves de API, IDs internos de base de datos ni tokens. El código de acceso (OTP) es la única excepción, y va con su vencimiento.

## Fórmulas por pieza

### Telegram / escritorio (señal)
```
🟢 Compra · BTC/USDT · 1h
Entrada $61.800,00 · SL $61.250,00 · TP $62.900,00
R/R 2,0:1 · Tamaño 0,0182 BTC
Bot #12 · Estrategia Tendencia EMA v1.0.0
```
(🔴 venta, ⚪ mantener). Sin otros emojis.

### Telegram / escritorio (otros eventos)
- **Precio**: `BTC/USDT cruzó $62.000,00 (sube)`.
- **Error de bot**: `El bot #12 se detuvo: no pudimos conectar con el exchange.` + qué revisar.

### Correo de código de acceso
- Asunto: `Tu código de acceso a Trading App`.
- Cuerpo: el código grande, cuándo vence (`Vence en 10 minutos`) y `Si no pediste este código, ignora este correo.`

### Correo de bienvenida
- Asunto: `Tu cuenta en Trading App está lista`.
- Cuerpo: con qué correo ingresa, cómo inicia sesión (contraseña o código) y a quién escribir si algo falla.

### Correo de alerta
- Asunto = la primera línea del mensaje de Telegram equivalente.
- Cuerpo: los mismos datos en una tabla corta y el enlace a la app.

## Ejemplos antes → después

| Antes | Después | Por qué |
|---|---|---|
| `¡Atención! Nueva señal 🚀🚀` | `🟢 Compra · BTC/USDT · 1h` | Qué y sobre qué, sin hype. |
| `Your OTP is 123456` | `Tu código de acceso es 123456. Vence en 10 minutos.` | Español, con vencimiento. |
| `Error en bot` | `El bot #12 se detuvo: no pudimos conectar con el exchange. Revisa las credenciales de la cuenta.` | Causa y paso siguiente. |
