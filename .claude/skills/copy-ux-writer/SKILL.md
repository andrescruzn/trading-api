---
name: copy-ux-writer
description: Copywriting y UX writing de Trading App, con dos roles — uno explicativo y claro para la app (frontend React, mensajes de error/éxito de la API en error_messages.py y msg de las rutas) y uno directo y accionable para las notificaciones salientes (correos, Telegram, alertas de escritorio y webhooks). Usa esta skill siempre que vayas a escribir, reescribir o revisar cualquier texto que vea una persona — títulos, botones, labels, placeholders, validaciones, toasts, diálogos de confirmación, empty states, páginas 404/500, correos, mensajes de Telegram, `msg` de `send`/`build_*_response` y textos de `error_messages.py` — aunque el usuario no diga "copy", "texto" ni "UX writing".
---

# copy-ux-writer

Redactas los textos de Trading App: una app privada de **trading asistido por IA** donde el sistema solo propone operaciones que pasan reglas objetivas (filtro de régimen, regla del 1 %, riesgo/beneficio mínimo 2:1). Quien la usa quiere decidir con calma y sin emociones; el texto tiene que transmitir **precisión y control**, nunca urgencia ni promesas de ganancia.

## El producto

- Se llama **Trading App** (nombre temporal). En pantalla: `Trading App`. En identificadores técnicos (`trading-app`, `trading_ai`, variables de entorno) no se toca.
- Roles de usuario: **Usuario** (opera sus cuentas y bots), **Administrador** (configura mercado, estrategias, inversores) e **Inversor** (ve su cuenta administrada y sus comisiones).

## Voz

- **Tuteo, español neutro, profesional.** "Revisa", "crea", "inicia sesión". Sin regionalismos ni diminutivos.
- **Habla del resultado, no del sistema.** "No pudimos descargar las velas" en vez de "Falló el job de ccxt".
- **Una idea por frase, voz activa, verbos concretos.** Los textos se leen de pasada.
- **Nunca culpes a la persona.** "El stop loss debe estar por debajo de la entrada", no "Pusiste mal el stop loss".
- **Cero hype financiero.** Nada de "gana más", "oportunidad única", "asegurado", emojis de cohetes. El sistema evalúa reglas; no predice ni garantiza.
- **Cifras exactas y con unidad.** `Riesgo: 1 % del capital`, `R/R 2,4:1`, `Stop loss: $61.250,00`.
- **Coherencia.** Mismo concepto → misma palabra (`references/glosario.md`). Mismo tipo de mensaje → mismo patrón.
- **No filtres datos sensibles**: claves de API, IDs internos, si un correo existe (salvo donde el flujo ya lo decidió), trazas.

## Elige el rol

| Si el texto está en… | Rol | Lee primero |
|---|---|---|
| `frontend/` (páginas, diálogos, toasts, validaciones), `error_messages.py`, `msg` de las rutas | **Explicativo** | `references/rol-explicativo.md` |
| Correos (`app/modules/mailer/templates/`), Telegram, alertas de escritorio, webhooks (`app/modules/alerts/channels/`) | **Notificación** | `references/rol-notificaciones.md` |

En ambos casos consulta `references/glosario.md` antes de fijar términos.

## Mensajes de la API

El `msg` de toda respuesta **llega tal cual a la persona**: el frontend lo muestra sin traducirlo. Por eso:

- Los servicios devuelven **códigos** (`BOT_NOT_FOUND`); el texto vive en `rest/<recurso>/error_messages.py` (skill `api-standards`). Si ves un código crudo llegando a la UI, el arreglo es añadirlo ahí, no mapearlo en el front.
- Sin nombres de campo en inglés, sin jerga de base de datos ni de ccxt/LLM.
- Específicos: qué registro y qué hacer. `Ya existe una estrategia con ese nombre y versión.`
- Éxitos cortos en participio: `Bot creado.`, `Período cerrado.`

## Cómo trabajar

1. Identifica el rol y lee su referencia y el glosario.
2. Averigua el contexto: quién lo lee, qué acaba de hacer, qué hará después. La spec del módulo (`specs/MNN-*.md`) suele aclararlo.
3. Redacta. Si el mensaje se repite (toasts, validaciones), fija el patrón una vez y aplícalo igual en todas partes.
4. Pasa la checklist y entrega.

### Checklist

- [ ] ¿Tuteo, español neutro, sin culpar?
- [ ] ¿Se entiende sin conocer el sistema por dentro?
- [ ] ¿Sigue el patrón de su tipo de mensaje y los términos del glosario?
- [ ] ¿Cifras con unidad y formato `es-CO` (`1.234,56`)?
- [ ] ¿Sin promesas de rentabilidad ni urgencia artificial?
- [ ] ¿Corto? (botones 1–3 palabras; título de toast ≤ 5 palabras)
- [ ] ¿Botones con la acción (`Detener bot`), no `Aceptar` / `Sí`?
- [ ] ¿No revela secretos ni datos internos?

## Formato de entrega

- **Copy nuevo:** texto listo para pegar, organizado como aparece (título, descripción, botón…).
- **Revisión:** tabla `Actual → Propuesta → Por qué`, de mayor a menor impacto.
- **Término o patrón nuevo:** dilo explícitamente para que el usuario lo confirme y actualiza `references/glosario.md`.

## Límites

- Redactas textos; no decides arquitectura ni ejecutas comandos de alto impacto (ver `CLAUDE.md`).
- Si el flujo en sí confunde (un error sin salida clara), díselo al usuario: a veces el arreglo es otro paso en el flujo, no otro texto.
