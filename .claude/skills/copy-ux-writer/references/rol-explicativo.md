# Rol explicativo: claro y guiado

Para el frontend (`frontend/`) y para los `msg` de la API (`error_messages.py` y `msg=` de las rutas), que la app muestra tal cual. Quien lee está operando o configurando: quiere terminar rápido y estar seguro de lo que hizo.

## Patrón base

**Qué pasó → por qué (solo si cambia lo que hay que hacer) → qué hacer ahora.**

- Si la persona puede arreglarlo, dile cómo. Si no, a quién acudir o qué esperar.
- Nada de lógica interna: tablas, IDs, códigos, nombres de librerías (ccxt, LLM provider).
- Las reglas de negocio se nombran cuando explican un rechazo: "La operación no cumple el riesgo/beneficio mínimo de 2:1".

## Patrones por tipo de mensaje

### Éxito (toast)
- **Título** en participio, específico: `Bot creado`, `Cambios guardados`, `Período cerrado`.
- **Descripción** solo si aporta: `Se calcularon 480 indicadores.`

### Error (toast o en pantalla)
- **Título contextual**: `No pudimos crear el bot`, nunca `Error`.
- **Descripción**: el `msg` de la API (`getErrorMessage(error)`), que ya sigue estas reglas. El respaldo local es `Revisa tu conexión e inténtalo de nuevo.`
- Error de carga de una sección: `ErrorAlert` con título `No pudimos cargar <la sección>`.

### Validación de formularios
- **Imperativo y positivo**: `Escribe el nombre`, `Elige el símbolo`, `Ingresa un correo válido`.
- Cuando el formato importa, di la regla: `Debe ser un número mayor que 0`, `Entre 1 y 1000 velas`.
- Placeholders con ejemplo real (`BTC/USDT`, `4h`), no repiten el label.

### Confirmación (acciones con efecto real)
- **Título** pregunta con el objeto: `¿Detener el bot #12?`, `¿Cerrar el período?`
- **Cuerpo**: la consecuencia: `El bot deja de generar señales. Las posiciones abiertas no se cierran.`
- **Botones**: verbo exacto + `Cancelar` (`Detener bot`, `Cerrar período`).
- Órdenes en **modo live**: siempre confirmar, mostrando lado, cantidad y precio.

### Empty state
- **Aún no hay datos**: para qué sirve + acción. `Aún no tienes bots. Crea uno para que genere señales con tu estrategia.` + `Nuevo bot`.
- **Filtros sin resultados**: `No hay órdenes con esos filtros.`
- **Falta un paso previo**: `Elige un bot para ver sus órdenes.`

### Carga y procesos largos
- Gerundio mientras pasa (`Analizando…`, `Descargando velas…`) y aviso si tarda: `El agente puede tardar hasta un minuto.`

### Sesión y permisos
- Sesión expirada: `Tu sesión expiró` / `Por seguridad la cerramos. Ingresa de nuevo para seguir.` → `Ingresar de nuevo`.
- Sesión revocada por otro login: `Tu sesión se cerró porque iniciaste sesión en otro lugar.`
- Sin permiso: `No tienes permiso para hacer esta acción.` Sin enumerar roles.

### Error inesperado (500)
- `Algo falló en el servidor. Inténtalo de nuevo en unos minutos.` Sin trazas.

## Mensajes de la API

- Español neutro; sin nombres de campo en inglés (`symbol_id`, `risk_pct`).
- El mismo código → el mismo texto en toda la API (reutiliza `COMMON_ERROR_MESSAGES` / `AUTH_ERROR_MESSAGES`).
- Validación Pydantic (422): el `msg` general ya es `Revisa los datos enviados…`; el front valida antes para que casi nunca llegue.
- Rechazos del agente o de las reglas de riesgo: di qué regla falló y el valor. `Riesgo/beneficio 1,6:1: por debajo del mínimo de 2:1.`

## Ejemplos antes → después

| Antes | Después | Por qué |
|---|---|---|
| `INVALID_CREDENTIALS` (código crudo) | `Correo o contraseña incorrectos.` | La API devuelve texto de UI. |
| Toast `Error` / `Request failed` | `No pudimos iniciar el bot` / msg de la API | Título con contexto. |
| `No hay bots.` | `Aún no tienes bots. Crea uno para que genere señales con tu estrategia.` | Explica y ofrece acción. |
| `¿Está seguro?` + `Sí` | `¿Detener el bot #12?` + `Detener bot` | El botón dice la acción. |
| `RR insuficiente` | `La operación no cumple el riesgo/beneficio mínimo de 2:1.` | Sin siglas en texto corrido. |
| `symbol_id is required` | `Elige el símbolo` | Sin nombres de campo. |
| `¡Señal generada con éxito! 🚀` | `Señal generada` | Sin hype ni emojis en la app. |
