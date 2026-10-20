# Módulo 9 — Alerts (Alertas) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 10/10 entregables (+ 3 de 2026-10-19: guarda SSRF, endurecimiento de Telegram, Telegram por usuario; + 1 de 2026-10-20: alertas que funcionan solas) |
| Madurez (estimada) | 71 % — ver [Avance](#avance) |
| Tablas | `alert_rules`, `alert_events` (R/W); `bots`, `signals`, `orders`, `accounts`, `signal_subscriptions` (R, vía hooks y propiedad); `users` (R: `telegram_chat_id`; R/W: `notifications_seen_at`) |
| Depende de | [M1](M01-AUTH.md) (vínculo del chat de Telegram), [M7](M07-BOTS-SIGNALS.md) y [M8](M08-ORDERS-EXECUTION.md) (hooks; Telegram aprueba/rechaza vía `ExecuteSignalService`); mailer para el canal email |
| Lo usan | Es un consumidor: lo invocan [M7](M07-BOTS-SIGNALS.md) (alertas + aviso de señal pendiente + señales compartidas), [M8](M08-ORDERS-EXECUTION.md) y el scheduler (reglas de precio, PnL y drawdown en cada ciclo + polling de Telegram) |
| Prefijo API | `/api/alert-rules`, `/api/alert-events`, `/api/alerts`, `/api/telegram/webhook`, `/api/notifications` |
| Frontend | `frontend/src/modules/alerts` (el vínculo de Telegram vive en `app-shell`, ver [M1](M01-AUTH.md)) |
| Última revisión | 2026-10-20 |

## Descripción

**En palabras simples:** Es el sistema de notificaciones. Te avisa cuando pasa algo importante, sin que tengas que estar mirando la pantalla todo el tiempo. Desde 2026-10-19 también es el **bot de Telegram** con el que apruebas o rechazas las señales de tus agentes en modo Con aprobación.

**Qué hace:**
- Define **reglas de alerta** personalizables por tipo:
  - `signal` → "Avísame cuando mi bot genere una señal BUY/SELL"
  - `price` → "Avísame si el precio de BTC/USDT baja de $80,000"
  - `pnl` → "Avísame si el P&L del bot baja del -5%"
  - `drawdown` → "Avísame si el drawdown supera el 10%"
  - `error` → "Avísame cuando el bot entre en error"
- Envía las alertas por **4 canales**: Email (SMTP), Telegram (Bot API), Webhook (HTTP POST a una URL externa **pública y https**) y Desktop (notificaciones nativas macOS/Windows/Linux con plyer)
- Las alertas se **disparan automáticamente** cuando se genera una señal (M7) o se crea una orden (M8), también si la orden fue rechazada
- Las reglas de **precio, PnL y drawdown se revisan solas** en cada ciclo del scheduler (cada minuto por defecto); mientras la condición siga, el aviso se repite como máximo cada `ALERT_REPEAT_MINUTES` (60 min), no en cada ciclo
- Por **Telegram**, las alertas llegan al chat que vinculó el dueño de la regla (si no vinculó ninguno, al chat del sistema); por **correo**, a su email
- Guarda un historial de todos los eventos de alerta disparados con estado de entrega
- El despacho es **fire-and-forget**: si falla una alerta, no afecta la operación de trading
- **Telegram por usuario:** cada persona vincula su chat privado; cuando un agente en modo Con aprobación tiene una señal pendiente, le llega un mensaje con los precios y botones **Aprobar** / **Descartar**. La respuesta se procesa por webhook (producción) o polling (desarrollo).
- **Señales compartidas** (2026-10-20): si un agente comparte sus señales ([M7](M07-BOTS-SIGNALS.md)), quienes lo siguen reciben por Telegram sus BUY/SELL aprobadas — solo información, sin botones.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/alerts` — Panel del usuario: reglas configuradas (crear/editar en diálogo, activar/desactivar) + historial de alertas recibidas
- Menú de usuario → **Conectar Telegram** (diálogo, [M1](M01-AUTH.md)): genera el enlace de vinculación con el bot

**Páginas — Administrador (solo admin):**
- `/#/admin/alerts` — "Todas las alertas" (Administración → Supervisión): todas las reglas y eventos del sistema, con columna **Dueño** (nombre y correo) y filtro por dueño (aplica a Reglas y a Eventos)
- `/#/admin/telegram` — "Telegram" (Administración → Configuración): ver la configuración y probar la conexión con Telegram Bot

## Entregables

Tablas: `alert_rules`, `alert_events`

Entregables:
- ✅ Domain: AlertRule entity + AlertEvent entity + Protocol repos
- ✅ Infrastructure: ORM models + repos impl registrados en models_registry.py
- ✅ Channels (Strategy Pattern): EmailChannel, TelegramChannel, WebhookChannel, DesktopChannel
- ✅ Services: FireAlertService, EvaluateAlertsService, CRUD alert_rules, list alert_events
- ✅ Provider: AlertServiceFactory + get_alert_factory() + build_evaluate_alerts_service()
- ✅ REST: GET/POST/PUT/DELETE /api/alert-rules, GET /api/alert-events, POST /api/alerts/evaluate, POST /api/alerts/test-telegram
- ✅ Hooks fire-and-forget en M7 (GenerateSignalService) y M8 (CreateOrderService)
- ✅ Web UI: `/#/alerts` (usuario), `/#/admin/alerts` (admin), `/#/admin/telegram` (config Telegram) — en React desde 2026-10-08
- ✅ Sidebar (`app-sidebar.tsx`) con links de Alertas y Telegram
- ✅ ALERT_TEMPLATE agregado al catálogo de mail templates
- httpx ya instalado (v0.28.1); plyer se instala opcionalmente para desktop notifications
- ✅ (2026-10-19) **Guarda SSRF del webhook** (`app/common/security/url_guard.py`) al guardar y al enviar; reglas solo sobre agentes propios; límite de claves en los JSON
- ✅ (2026-10-19) **Telegram endurecido**: HTML escapado, token nunca en logs, helper `telegram_api`
- ✅ (2026-10-19) **Telegram por usuario**: `SignalApprovalNotifier` (botones), `TelegramUpdateService`, `TelegramReplier`, `telegram_messages.py`, `telegram_poller.py`, `POST /api/telegram/webhook`, `telegram_provider.py`
- ✅ (2026-10-20) **Señales compartidas**: `SharedSignalNotifier` + `shared_signal_text` + `build_shared_signal_notifier` (hook `notify_subscribers` de [M7](M07-BOTS-SIGNALS.md)), 10 tests
- ✅ (2026-10-20) **Alertas que funcionan solas**: `EvaluatePeriodicAlertsService` (precio, PnL y drawdown) como paso `_evaluate_alert_rules` del ciclo de ejecución, antispam `ALERT_REPEAT_MINUTES`, `domain/rule_conditions.py`, `channels/alert_messages.py`; Telegram al chat del dueño y correo al dueño en `FireAlertService`; 44 tests en `tests/alerts/`
- ✅ (2026-10-20) **Notificaciones en la app**: campana en la cabecera con los últimos `alert_events` del usuario y contador de no leídas; el "visto" se guarda en la cuenta (`users.notifications_seen_at`, [M1](M01-AUTH.md)), así vale en todos los dispositivos. Ver [Notificaciones en la app](#notificaciones-en-la-app-campana)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Canales como **Strategy Pattern** (`NotificationChannel` Protocol: Email, Telegram, Webhook, Desktop) | Añadir un canal no toca el motor de alertas | `if channel == ...` |
| Despacho **fire-and-forget**: los hooks van en `try/except pass` | Una alerta fallida nunca aborta el flujo de trading | Propagar el error |
| Hooks **post-commit** en [M7](M07-BOTS-SIGNALS.md) (`evaluate_signal_alerts`) y [M8](M08-ORDERS-EXECUTION.md) (`evaluate_order_alerts`) | Solo se alerta de lo que ya quedó persistido | Disparar antes del commit |
| `build_evaluate_alerts_service(session)` + `TYPE_CHECKING` en M7/M8 | Evita imports circulares entre M7/M8 y M9 | Importar la factory directamente |
| Cada disparo se guarda como `alert_events` con `delivery_status` (`pending` / `sent` / `failed`) | Historial auditable de lo enviado y lo fallido | Solo enviar sin registrar |
| Borrado **lógico** de reglas (`DELETE` → `is_active=False`) | Conserva el historial de eventos asociado | Borrado físico |
| Visibilidad por propietario: el usuario ve sus reglas, el admin todas (con *ownership check* en detalle/edición) | Aislamiento entre usuarios | Reglas globales |
| Una regla con `bot_id` exige que el agente sea del usuario (`find_accessible_bot` → `BOT_NOT_FOUND` 404) | Antes se podía crear una regla sobre el agente de otro y recibir sus señales | Solo validar que el bot exista |
| **Webhook contra SSRF en dos pasos:** al guardar (`is_allowed_webhook_url`: solo `https`, sin usuario/contraseña, ≤ 2048 caracteres, sin `localhost`/`*.internal`/`metadata.google.internal`, nombres con punto, IP literal pública) y al enviar (`resolves_to_public_ips`: todas las IPs resueltas deben ser públicas) | Un dominio público puede apuntar a `127.0.0.1` o a la red interna; validarlo solo al guardar no basta | Solo comprobar `startswith("http")` (antes) |
| Webhook con `follow_redirects=False`, timeout 5 s y **la URL nunca en los logs** (se loguea el `rule.id`) | Un 302 hacia una IP interna no se sigue; las URLs de Slack/Discord llevan el token en la ruta | Seguir redirects y loguear la URL |
| Telegram con `parse_mode=HTML` y `html.escape` en todo texto variable | Un nombre de regla con `*` o `<` rompía el Markdown anterior | `parse_mode=Markdown` sin escapar |
| `telegram_api(token, method, payload)` único para la Bot API: loguea método, status y `description` (≤ 200), nunca la URL ni el texto de la excepción | El token va en la URL y httpx lo incluye en sus excepciones | Un `httpx.post` por canal |
| Telegram de **alertas** al chat vinculado del **dueño de la regla** (`users.telegram_chat_id`); sin vínculo (o si falla la lectura del usuario) cae en `TELEGRAM_DEFAULT_CHAT_ID` | Cada quien recibe sus avisos en su chat; el respaldo mantiene el comportamiento anterior para quien no vinculó | Solo el chat del sistema (antes) / no enviar sin vínculo |
| Correo de alertas: el del request si lo hay; si no (hooks, scheduler, endpoint admin), el del **dueño de la regla** | Antes los hooks no tenían correo y el canal email nunca enviaba | Pasar el correo desde cada hook |
| Reglas `price`/`pnl`/`drawdown` evaluadas en el **ciclo de ejecución** del scheduler (`_evaluate_alert_rules`, sesión propia, después de proteger posiciones), con los datos ya guardados | No llama a exchanges ni a la IA; tras los cierres por SL/TP el PnL ya está al día | Endpoint manual (antes) / job aparte |
| **Antispam por cooldown** con el último `alert_events` de la regla: si tiene menos de `ALERT_REPEAT_MINUTES` (60), la regla ni se evalúa | Sin columnas nuevas; mientras la condición siga, es un recordatorio cada N minutos | Transición falso→verdadero (exige guardar el estado "falso") |
| Precio = cierre de la **vela más reciente del símbolo** en BD, de cualquier timeframe | La regla no guarda timeframe; la vela más nueva es el último precio conocido | Pedir timeframe en la regla |
| Base de los % de PnL y drawdown = **capital invertido**: la mayor inversión del agente en una sola operación (costo de cada operación cerrada y de lo abierto) | En spot hay una operación a la vez: es "lo que pone en juego"; sumar todas las compras diluiría el % con cada operación | Suma de costos / saldo de la cuenta |
| Drawdown **actual** (pico del PnL acumulado − PnL de ahora, con lo no realizado), no el máximo histórico | El máximo histórico nunca baja: la regla quedaría disparando para siempre | `Performance.max_drawdown` |
| PnL `daily` = cambio del PnL total desde las 00:00 **hora de Bogotá** (fills hasta esa hora + último cierre antes de esa hora) | Es el día que ve la persona en la app | Día UTC |
| Reglas `pnl`/`drawdown` **exigen agente** (`ALERT_RULE_BOT_REQUIRED` 422); las antiguas sin agente se omiten | Miden un agente concreto; "cualquier agente" no tiene una cifra única | Evaluar cada agente del dueño |
| `POST /api/alerts/evaluate` reutiliza `EvaluatePeriodicAlertsService.evaluate_price` (mismo antispam); `EvaluateAlertsService` queda solo para hooks de señal/orden | Una sola lógica de precio | Mantener dos evaluadores |
| Vínculo del chat por enlace `https://t.me/<bot>?start=<código>` de un solo uso (10 min, guardado como SHA-256) — servicio en [M1](M01-AUTH.md) | La persona no copia IDs; el código no queda en claro en BD | Pedir el `chat_id` a mano |
| Aviso de señal pendiente con **botones inline** `sig:a:<id>` / `sig:r:<id>`; "Ver en Trading App" solo si `FRONTEND_URL` empieza por `https://` | Aprobar con un toque; Telegram rechaza botones con enlaces a localhost | Responder con texto ("SI 123") |
| `TelegramUpdateService` solo entiende `/start <código>` y los `callback_data` con formato fijo, solo en **chats privados**; la identidad sale del chat vinculado y la señal debe ser de un agente de ese usuario (también si es admin) | El texto de la persona nunca se interpreta; desde Telegram cada quien decide lo suyo | Comandos libres |
| Tras decidir, se responde con `answerCallbackQuery` y se reescribe el mensaje original con el resultado (`editMessageText`) | Queda claro en el chat qué pasó con la señal | Mandar un mensaje nuevo |
| Textos del bot en `telegram_messages.py` (`DECISION_MESSAGES`, `LINK_MESSAGES`, botones), con números `es-CO` y hora de Bogotá | Igual que `error_messages.py`: los servicios devuelven códigos | Textos dentro de los servicios |
| Tres modos de recibir respuestas (`TELEGRAM_UPDATES_MODE`): `off` · `polling` (el scheduler líder llama `getUpdates`; desarrollo) · `webhook` (Telegram llama `POST /api/telegram/webhook`; producción) | En desarrollo Telegram no puede llamar a localhost | Solo webhook |
| Webhook protegido con `X-Telegram-Bot-Api-Secret-Token` comparado en tiempo constante con `TELEGRAM_WEBHOOK_SECRET`; sin secreto o con otro modo → 404; con secreto correcto → siempre 200 | Solo Telegram puede llamarlo; con otro código Telegram reintenta el mismo update | Endpoint abierto |
| `/api/telegram/webhook` **excluido de la auditoría HTTP** | El cuerpo de `/start` lleva el código de vinculación y mensajes de terceros | Auditarlo con redacción |
| `SharedSignalNotifier`: mensaje **sin botones**, sin tamaño de posición, cuenta ni nombre del agente (acción, símbolo, timeframe, entrada, SL, TP, R/R y estrategia); omite al dueño y a quien no tiene chat; nunca lanza (log por suscriptor y por llamada) | Quien sigue no decide ni ejecuta nada; el tamaño revela el capital del dueño y el nombre puede identificarlo; un chat roto no corta el reparto | Reutilizar `pending_signal_text` |
| `telegram_provider.py` no se exporta en `providers/__init__.py` y hace imports diferidos de los providers de orders y users | `orders → alerts` (hooks) importa este paquete: un import a nivel de módulo crearía un ciclo | Reorganizar los paquetes |
| El email usa `ALERT_TEMPLATE` del catálogo del mailer (`alert.html`) | Reutiliza el servicio SMTP existente | Plantilla embebida |
| Notificaciones de escritorio (`plyer`) **opcionales** (`DESKTOP_NOTIFICATIONS_ENABLED=false`) | Solo tiene sentido en desarrollo local | Dependencia obligatoria |
| `admin_required` importado de `role_guard` (no `role_guard(settings.AUTH_ADMIN_ROLE_ID)`) | Convención del proyecto | — |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (10/10) | Dominio, infraestructura, 4 canales, servicios, REST, hooks y UI usuario + admin. Además, 3 entregables nuevos (2026-10-19) |
| Madurez | **≈ 71 %** | Funcionalidad 92 · Tests 35 · Seguridad 85 · Operación 72 |

- **Funcionalidad (92):** los 5 tipos de regla se evalúan: `signal`/`error` en los hooks de M7/M8 y `price`/`pnl`/`drawdown` solos en cada ciclo del scheduler (`_evaluate_alert_rules` → `EvaluatePeriodicAlertsService`), con antispam. Telegram de alertas al chat del dueño y correo al dueño (`FireAlertService`). Las reglas `signal`/`error` con "Cualquier agente" (`bot_id` NULL) aplican a todos los agentes de su dueño (`list_active_by_type_and_bot` con subquery bots → accounts.user_id). Falta: reintentos de entregas `failed`.
- **Tests (35):** 44 tests en `tests/alerts/` de la evaluación periódica (condiciones, servicio, antispam, ruteo de Telegram/correo, paso del scheduler) + `SharedSignalNotifier` (10) + campana (7). Sin cubrir: `url_guard`, `TelegramUpdateService`, hooks `signal`/`error` y canales email/webhook/desktop.
- **Seguridad (85):** guarda SSRF al guardar y al enviar, sin redirects; reglas solo sobre agentes propios; JSON con máximo 20 claves; HTML escapado y token fuera de los logs; webhook de Telegram con secreto. Riesgo residual de *DNS rebinding* entre la resolución y la conexión (ver [Riesgos](#riesgos)).
- **Operación (72):** las reglas periódicas corren solas en el scheduler líder, con errores aislados por regla y un log por ciclo cuando algo se dispara o falla; polling de Telegram en desarrollo y webhook en producción (registro manual con `setWebhook`). El canal Desktop solo notifica en la máquina del servidor.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Media | Tests de `url_guard`, `FireAlertService`, `EvaluateAlertsService`, `TelegramUpdateService` (callbacks, `/start`, chat no vinculado) y de cada canal con HTTP/SMTP mockeado | M |
| Media | Reintentos y *backoff* para entregas `failed` | M |
| Media | Disparo por **transición** (avisar solo cuando la condición pasa de falsa a verdadera) en vez de cooldown; requiere guardar el último estado de la regla | M |
| Media | No evaluar `price` con velas viejas (descarga caída): omitir si la vela más reciente supera N timeframes | S |
| Baja | Mostrar en `/#/alerts` el valor actual de cada regla periódica (precio, PnL %, drawdown %) | M |
| Media | Deduplicación / agrupación de alertas (un bot en error no debe generar una alerta por ciclo) | M |
| Media | Cerrar el *DNS rebinding* del webhook: conectar a la IP ya validada o pasar por un proxy de salida que filtre IPs | M |
| Baja | Persistir el `offset` del polling (hoy en memoria; tras reiniciar Telegram reenvía lo no confirmado ≤ 24 h) | S |
| Baja | Plantillas por canal | M |
| Baja | Botón en `/#/admin/alerts` para `POST /api/alerts/evaluate` (hoy solo por API; el front no lo llama) | S |

## Fuera de alcance y pendientes conocidos

- Canales adicionales (SMS, WhatsApp, Slack, Discord).
- Aviso por Telegram de las órdenes que ejecuta un agente Automático (solo se avisan las señales por aprobar).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `alert_rules` | WRITE | Reglas configuradas por usuario/bot |
| `alert_events` | WRITE | Historial de alertas disparadas |
| `bots` | READ (hook) | Para evaluar reglas tipo 'signal'/'error' y validar la propiedad al crear |
| `accounts` | READ | Propiedad del agente (bot → cuenta → usuario) |
| `signals` | READ (hook) | Datos de la señal para el payload |
| `orders` | READ (hook) | Datos de la orden para el payload |
| `users` | READ | `telegram_chat_id` del dueño del agente (aviso), del chat que responde (decisión) y de los suscriptores (señales compartidas); columnas de [M1](M01-AUTH.md) |
| `signal_subscriptions` | READ | Suscriptores de un agente compartido (tabla de [M7](M07-BOTS-SIGNALS.md)) |

### Modelos ORM (`app/modules/alerts/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `alert_rule_model.py` | `AlertRuleModel` | `alert_rules` |
| `alert_event_model.py` | `AlertEventModel` | `alert_events` |

### Repositorios
| Domain (Protocol) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/alert_rule_repository.py` | `infrastructure/alert_rule_repository_impl.py` → `SqlAlchemyAlertRuleRepository` |
| `domain/alert_event_repository.py` | `infrastructure/alert_event_repository_impl.py` → `SqlAlchemyAlertEventRepository` |

`AlertRule.webhook_url` devuelve la URL solo si pasa `is_allowed_webhook_url`; `has_valid_webhook()` la valida al crear y al editar (`ALERT_RULE_INVALID_WEBHOOK` 422).

### Canales (`app/modules/alerts/channels/`)
| Archivo | Clase / función | Canal |
|---------|-------|-------|
| `channel_interface.py` | `NotificationChannel` (Protocol) | Contrato |
| `email_channel.py` | `EmailChannel` | SMTP via MailerService |
| `telegram_channel.py` | `TelegramChannel` (`send`, `send_raw`, `call(method, payload)`) + `telegram_api(token, method, payload)` | Bot API via httpx (timeout 10 s); devuelve el `result` o `None` |
| `webhook_channel.py` | `WebhookChannel` | HTTP POST via httpx; `resolves_to_public_ips` antes de cada envío, sin redirects, timeout 5 s |
| `desktop_channel.py` | `DesktopChannel` | plyer (macOS/Win/Linux) |
| `telegram_messages.py` | `DECISION_MESSAGES`, `LINK_MESSAGES`, `BUTTON_APPROVE/REJECT/OPEN_APP`, `pending_signal_text(...)`, `shared_signal_text(...)`, `decision_text(code)`, `format_number` | Textos del bot (rol notificación) |
| `telegram_replier.py` | `TelegramReplier` (`link_result`, `decision_result`) | Responde con `sendMessage`, `answerCallbackQuery` y `editMessageText` |
| `telegram_poller.py` | `fetch_updates(token)` | `getUpdates` con `offset` en memoria (modo polling) |

### Guarda SSRF (`app/common/security/url_guard.py`)
- `is_allowed_webhook_url(url)` — validación estática (sin red), al guardar.
- `resolves_to_public_ips(url)` — `getaddrinfo` del host: todas las IPs deben ser `is_global` y no multicast (IPv4 mapeadas a IPv6 se evalúan como IPv4), al enviar.

### Servicios (`app/modules/alerts/services/`)
| Subdir | Servicios |
|--------|-----------|
| `alert_rules/` | `list_alert_rules_service.py`, `create_alert_rule_service.py` (`owner_id`, bot propio, webhook válido), `update_alert_rule_service.py` (webhook válido) |
| `alert_events/` | `list_alert_events_service.py` |
| `evaluation/` | `fire_alert_service.py` (crea evento + despacha; Telegram al chat del dueño, correo al dueño), `evaluate_alerts_service.py` (hooks: reglas `signal`/`error`), `evaluate_periodic_alerts_service.py` (`run()` del scheduler y `evaluate_price()` del endpoint manual → `PeriodicAlertsReport(checked, fired, cooldown, skipped, failed)`) |
| `telegram/` | `signal_approval_notifier.py` (`SignalApprovalNotifier.notify(signal, bot)`: sin token, sin cuenta o sin chat vinculado no envía), `shared_signal_notifier.py` (`SharedSignalNotifier.notify(signal, bot) -> int` enviados: sin token, agente que no comparte o señal no accionable → 0), `telegram_update_service.py` (`TelegramUpdateService.handle(update)`: `/start <código>` → `TelegramLinkService.confirm`; `sig:a:<id>` / `sig:r:<id>` → `ExecuteSignalService.execute/reject(channel="telegram")`) |

Providers:
- `app/modules/alerts/providers/alert_provider.py` → `AlertServiceFactory` (`evaluate_periodic_alerts()` con imports diferidos de bots/orders), `get_alert_factory()`, `build_evaluate_alerts_service()`, `build_periodic_alerts_service(session)` (scheduler)
- `app/modules/alerts/providers/telegram_provider.py` → `build_signal_approval_notifier(session)` y `build_shared_signal_notifier(session)` (los usa `BotServiceFactory.generate_signal()`), `build_telegram_update_service(session)` (`None` sin `TELEGRAM_BOT_TOKEN`; lo usan el webhook y el polling)

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/alert-rules` | token | Admin ve todas; user ve las suyas |
| POST | `/api/alert-rules` | token | Crea regla; `bot_id` debe ser un agente propio; webhook https público; `rule_spec`/`channels` ≤ 20 claves |
| GET | `/api/alert-rules/{id}` | token | Detalle; ownership check |
| PUT | `/api/alert-rules/{id}` | token | Actualiza regla; ownership check; webhook validado |
| DELETE | `/api/alert-rules/{id}` | token | Soft delete (is_active=False) |
| GET | `/api/alert-events` | token | Historial de eventos |
| POST | `/api/alerts/evaluate` | admin | Reglas `price` de un símbolo con el precio dado (`{symbol_id, current_price}`), mismo antispam → `{fired, checked, cooldown}` |
| POST | `/api/alerts/test-telegram` | admin | Test de conexión Telegram |
| POST | `/api/telegram/webhook` | cabecera `X-Telegram-Bot-Api-Secret-Token` | Updates del bot (solo con `TELEGRAM_UPDATES_MODE=webhook`); fuera de Swagger (`include_in_schema=False`) y de la auditoría |
| GET | `/api/notifications?limit=20` | token | Campana: `{items: [{id, ts, title, message, severity, bot_id, is_new}], unread_count, seen_at}`; solo eventos propios (también para un admin); `limit` 1–50; `ts` en UTC con offset |
| POST | `/api/notifications/seen` | token | `users.notifications_seen_at = utc_now()` → `{seen_at}` |

Los routers declaran `prefix="/alert-rules"`, `"/alert-events"`, `"/alerts"`, `"/telegram"`; el `/api` lo añade `app_factory.py` (`settings.API_PREFIX`).

**Registro del webhook** (una vez, lo hace el administrador; está en la cabecera de `rest/telegram_webhook/routes.py`):
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://<api>/api/telegram/webhook" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>" \
  -d 'allowed_updates=["message","callback_query"]'
```
Para volver a polling hay que borrar el webhook (`deleteWebhook`): `getUpdates` no funciona con un webhook registrado.

### Frontend (`frontend/src/modules/alerts/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/alerts` | `routes/_app/alerts.lazy.tsx` | `pages/alerts.tsx` (`AlertsPage`) + `components/alert-rule-form-dialog.tsx` + `components/alert-events-table.tsx` |
| `/#/admin/alerts` | `routes/_app/admin/alerts.lazy.tsx` | `pages/admin-alerts.tsx` + `components/alert-events-table.tsx` |
| `/#/admin/telegram` | `routes/_app/admin/telegram.lazy.tsx` | `pages/admin-telegram.tsx` |

- API: `api/alerts.api.ts` (`/alert-rules`, `/alert-events`, `/alerts/test-telegram`); hooks `use-alerts-queries.ts` / `use-alerts-mutations.ts`; etiquetas `lib/alerts-labels.ts`; badges `components/alert-badges.tsx`.
- Activar/desactivar una regla se hace con `PUT /api/alert-rules/{id}` (`is_active`); el front no usa `DELETE` ni `POST /api/alerts/evaluate`.
- Nombres de bot: `useMyBotsQuery` de [M7](M07-BOTS-SIGNALS.md) en páginas de usuario y `useBotsQuery()` en admin.
- Vincular Telegram: `app-shell/components/telegram-link-dialog.tsx` ([M1](M01-AUTH.md)).
- Campana: `components/notifications-bell.tsx` en la cabecera de `app-shell/layouts/app-shell.tsx`; `api/notifications.api.ts`, `useNotificationsQuery` (polling 60 s + al volver a la pestaña) y `useMarkNotificationsSeenMutation`.

### Notificaciones en la app (campana)

- **Fuente:** `alert_events` del usuario (cada regla disparada crea uno). No hay tabla nueva.
- **No leídas:** eventos con `ts > users.notifications_seen_at`; con `NULL` (nunca abrió la campana) todos lo son. `unread_count` cuenta todos los nuevos, no solo los listados (`AlertEventRepository.count_by_user_after`).
- **Servicios** (`services/notifications/`): `ListNotificationsService.list(user_id, limit)` → `NotificationFeed(items, unread_count, seen_at)`; `MarkNotificationsSeenService.mark_seen(user_id)` → `UserRepository.set_notifications_seen_at` (UPDATE de esa sola columna, no pisa el JTI) + `commit()`. `USER_NOT_FOUND` 404 en `rest/notifications/error_messages.py`.
- **Wiring:** `AlertServiceFactory.list_notifications()` / `mark_notifications_seen()` toman prestado `SqlAlchemyUserRepository`.
- **Front:** badge con el contador (9+), `aria-label` "Notificaciones: N sin leer"; al abrir se marca como visto (solo si hay pendientes) y las que eran nuevas siguen resaltadas mientras el panel esté abierto; punto de color por severidad (`chart-2` / `chart-3` / `destructive`); "Ver todas" → `/#/alerts`; vacío explica que vienen de las reglas de alerta, con "Crear una regla".

### Reglas periódicas (precio, PnL, drawdown)

Las evalúa `EvaluatePeriodicAlertsService.run()` en el paso `_evaluate_alert_rules` del ciclo de ejecución (scheduler líder). Lógica pura en `domain/rule_conditions.py`; textos en `channels/alert_messages.py`.

| Tipo | `rule_spec` | Se dispara cuando |
|---|---|---|
| `price` | `{symbol_id, operator: lt\|lte\|gt\|gte, threshold}` | El cierre de la vela más reciente del símbolo (cualquier timeframe) cumple `operator threshold` |
| `pnl` (con agente) | `{threshold (%), period: total\|daily}` | Umbral < 0: PnL % ≤ umbral (pérdida). Umbral ≥ 0: PnL % ≥ umbral |
| `drawdown` (con agente) | `{threshold (%) > 0}` | Drawdown actual % ≥ umbral |

- **PnL total** = realizado de las operaciones cerradas + ventas parciales de la abierta + no realizado de lo abierto al último cierre del símbolo/timeframe del agente (`compute_performance` de [M8](M08-ORDERS-EXECUTION.md)).
- **Capital invertido** (base de los %) = máx(costo de compra de cada operación cerrada, `open_qty × open_avg_price`).
- **PnL % total** = PnL total / capital invertido × 100. **PnL % diario** = (PnL total ahora − PnL total a las 00:00 de Bogotá) / capital invertido × 100; el PnL de las 00:00 usa los fills anteriores y la última vela antes de esa hora.
- **Drawdown actual** = máx(0, pico del PnL acumulado de las operaciones cerradas, desde 0) − PnL total; en % sobre el capital invertido.
- **Ejemplo:** operaciones cerradas de +40 (costo 1.000) y −20 (costo 800) y una abierta de 0,01 a 60.000 (costo 600) con último cierre 57.000 (−30) → PnL total −10 = **−1 %**; pico 40 → drawdown 50 = **5 %** (dispara una regla de 5).
- **Antispam:** si `alert_events` tiene un evento de la regla de hace menos de `ALERT_REPEAT_MINUTES`, la regla no se evalúa (`cooldown`). Sin datos (sin velas, sin agente, sin operaciones, spec inválida) → `skipped`.
- Severidad: `price` → warning; `pnl` → warning si el umbral es negativo, info si es positivo; `drawdown` → critical.

### Hooks en otros módulos
- `app/modules/bots/services/signals/generate_signal_service.py` — hook post-commit: `evaluate_alerts.evaluate_signal_alerts()` y, si la señal queda `pending` en modo `approval`, `notify_pending(signal, bot)`
- `app/modules/orders/services/orders/create_order_service.py` — hook post-commit: `evaluate_alerts.evaluate_order_alerts()` (también tras un rechazo)
- `app/modules/bots/providers/bot_provider.py` — inyecta `build_evaluate_alerts_service(session)` y `build_signal_approval_notifier(session).notify` en `generate_signal()`
- `app/modules/orders/providers/order_provider.py` — inyecta `build_evaluate_alerts_service(session)` en `create_order()`
- `app/modules/scheduler/execution_cycle.py` — paso 5 `_evaluate_alert_rules()` (reglas periódicas, sesión propia, después de `_protect_positions`) y paso 6 `_poll_telegram()` en modo polling

### Settings (`.env`)
```
TELEGRAM_BOT_TOKEN=<token>          # de @BotFather; vacío = Telegram inactivo
TELEGRAM_DEFAULT_CHAT_ID=<chat_id>  # chat de las alertas
TELEGRAM_BOT_USERNAME=              # @usuario del bot sin @ (enlace t.me/<bot>?start=...)
TELEGRAM_UPDATES_MODE=off           # off | polling (desarrollo) | webhook (producción)
TELEGRAM_WEBHOOK_SECRET=            # secret_token de setWebhook; obligatorio con webhook
FRONTEND_URL=http://localhost:5193  # enlaces en Telegram (botón solo si es https)
DESKTOP_NOTIFICATIONS_ENABLED=false
ALERT_REPEAT_MINUTES=60            # antispam de precio/PnL/drawdown; 0 = avisa en cada ciclo
```

## Gotchas críticos

- `admin_required` se importa de `app.common.security.jwt.role_guard` (NO usar `role_guard(settings.AUTH_ADMIN_ROLE_ID)`)
- `build_evaluate_alerts_service(session)` evita imports circulares entre M7/M8 y M9; **no** exportar `telegram_provider` en `providers/__init__.py` (crea el ciclo orders → alerts → orders)
- `TYPE_CHECKING` guard en `generate_signal_service.py` y `create_order_service.py` para evitar import circular en runtime
- Los hooks siempre en `try/except` — las alertas nunca abortan el flujo de trading
- **Webhooks a servicios internos:** una regla con `http://`, `localhost`, una IP privada o un nombre sin punto se rechaza al guardar (`ALERT_RULE_INVALID_WEBHOOK`); si el DNS cambia después hacia una IP interna, el envío se bloquea y el evento queda `failed` (log `URL bloqueada (no pública) en la regla <id>`).
- **Telegram no responde a los botones:** revisar `TELEGRAM_UPDATES_MODE` (con `off` no se procesa nada), que en polling no haya un webhook registrado y que en webhook coincida `TELEGRAM_WEBHOOK_SECRET`.
- **Polling solo en el líder:** el `offset` vive en memoria del proceso líder del scheduler; tras reiniciar, Telegram reenvía lo no confirmado (seguro: decidir es atómico y los códigos de vínculo son de un solo uso).
- **Sin `FRONTEND_URL` https** el aviso no lleva el botón "Ver en Trading App" (Telegram rechaza enlaces a localhost).
- El email de alerta usa `ALERT_TEMPLATE` desde `app.modules.mailer.domain.mail_template`
- Template HTML en `app/modules/mailer/templates/alert.html`
- `httpx` ya instalado (v0.28.1) — `plyer` opcional para desktop

## Tests

- `tests/bots/test_shared_signal_notifier.py` — 10 tests de `SharedSignalNotifier` (envío sin botones, sin nombre ni tamaño, omite dueño/sin chat/HOLD/rechazadas/agente que no comparte/sin token, fallo de envío tragado). El resto del módulo no tiene tests.
- `tests/alerts/test_notifications_service.py` — 7 tests de la campana (no leídas con `NULL` y con fecha, `limit` acotado, aislamiento por usuario, usuario inexistente, marcar visto confirma / revierte).
- `tests/alerts/test_rule_conditions.py` — 16 tests: precio en ambos sentidos, snapshot de PnL/drawdown con el ejemplo de la cabecera, venta parcial, sin operaciones, PnL diario, umbrales y cooldown (incluye fecha naive de MySQL).
- `tests/alerts/test_evaluate_periodic_alerts_service.py` — 17 tests: precio `lt`/`gt` con la vela más reciente, sin velas, endpoint manual; PnL total −5 %, diario (−3,33 % no dispara / −5 % sí), positivo; sin agente o sin operaciones se omite; drawdown 5 % dispara y 3 % no; cooldown 30 min / 61 min / 0; error de una regla no frena a otra (rollback).
- `tests/alerts/test_fire_alert_routing.py` — 7 tests: chat del dueño, respaldo al chat del sistema (sin vínculo o si falla la lectura), envío fallido → `failed`, correo al dueño o al del request.
- `tests/alerts/test_execution_cycle_alerts.py` — 4 tests: sesión propia que siempre se cierra, fallo aislado de los demás pasos, orden después de `_protect_positions`.
- Recomendado: `url_guard` (IPs privadas, IPv4 mapeada, `.internal`, puertos), hooks `signal`/`error` de `EvaluateAlertsService`, `TelegramUpdateService` y los canales con dependencias mockeadas.

## Riesgos

- **DNS rebinding:** entre la resolución DNS y la conexión del webhook hay una ventana (TTL 0). Riesgo residual bajo con redirects desactivados; cerrarlo del todo exige un proxy de salida que filtre IPs.
- Alertas silenciosas: los hooks tragan cualquier excepción; si el canal está mal configurado, nadie se entera salvo por `alert_events.delivery_status = failed`.
- Un usuario podría configurar muchas reglas: el cooldown limita cada regla a un aviso por `ALERT_REPEAT_MINUTES`, pero no hay tope de reglas por usuario.
- **Chat del sistema como respaldo:** si el dueño no vinculó Telegram, su alerta llega a `TELEGRAM_DEFAULT_CHAT_ID` (lo ve quien administre ese chat). Dejar `TELEGRAM_DEFAULT_CHAT_ID` vacío para no enviar nada sin vínculo.
- Con `ALERT_REPEAT_MINUTES` el aviso es un recordatorio periódico mientras la condición siga: una regla de precio que queda cumplida días enteros avisa cada hora.
- Quien controle el chat de Telegram vinculado puede aprobar las señales de esa cuenta: desvincularlo desde el menú de usuario si se pierde el teléfono.

## Historial

- **2026-03** — Módulo completado: 4 canales, reglas y eventos, hooks en M7/M8, UI `/alerts`, `/admin/alerts`, `/admin/telegram`, plantilla `ALERT_TEMPLATE`.
- **Dependencias:** `httpx` 0.28.1 ya instalado; `plyer` opcional.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-10** — Seed `alerts`: tres reglas demo (señal y drawdown del 5 % del agente de oro, error del agente de BTC), solo canal de escritorio, idempotente por (user_id, name).
- **2026-10-19** — Auditoría de seguridad: guarda SSRF del webhook (`url_guard.py`: https, hosts públicos, resolución DNS al enviar, sin redirects, URL fuera de los logs; `ALERT_RULE_INVALID_WEBHOOK`), reglas solo sobre agentes propios, límite de claves en los JSON; Telegram con HTML escapado, token fuera de los logs y helper `telegram_api`.
- **2026-10-19** — Telegram por usuario para el modo Con aprobación: `SignalApprovalNotifier` (botones `sig:a`/`sig:r`), `TelegramUpdateService`, `TelegramReplier`, `telegram_messages.py`, `telegram_poller.py` (polling en el scheduler), `POST /api/telegram/webhook` con secreto (fuera de la auditoría), `telegram_provider.py`; settings `TELEGRAM_BOT_USERNAME`, `TELEGRAM_UPDATES_MODE`, `TELEGRAM_WEBHOOK_SECRET`, `FRONTEND_URL`.
- **2026-10-20** — Todas las alertas: columna **Dueño** (nombre y correo) y filtro por dueño en Reglas y Eventos; Telegram pasa al grupo admin **Configuración**.
- **2026-10-20** — **Señales compartidas** ([M7](M07-BOTS-SIGNALS.md)): `SharedSignalNotifier` envía a los suscriptores de un agente compartido sus BUY/SELL aprobadas por Telegram, sin botones ni datos de la cuenta; `shared_signal_text`, `build_shared_signal_notifier`. Primeros tests del módulo (`tests/bots/test_shared_signal_notifier.py`).
- **2026-10-20** — **Notificaciones en la app**: campana en la cabecera (`GET /api/notifications`, `POST /api/notifications/seen`), estado de "visto" en `users.notifications_seen_at` (migración `45ba83355691`), polling cada 60 s, 7 tests.
- **2026-10-20** — **Alertas que funcionan solas**: las reglas `price`, `pnl` y `drawdown` se evalúan en cada ciclo del scheduler (`_evaluate_alert_rules` → `EvaluatePeriodicAlertsService`, `rule_conditions.py`, `alert_messages.py`); PnL y drawdown en % del capital invertido (mayor inversión de una operación), PnL `daily` desde las 00:00 de Bogotá, drawdown actual desde el pico; antispam `ALERT_REPEAT_MINUTES` (60) con el último evento de la regla; Telegram al chat del dueño (respaldo: chat del sistema) y correo al dueño; `pnl`/`drawdown` exigen agente (`ALERT_RULE_BOT_REQUIRED`); `POST /api/alerts/evaluate` reutiliza el servicio; front: agente obligatorio y textos de revisión automática. 44 tests en `tests/alerts/`. Sin cambios de esquema.
- **2026-10-20** — Reglas `signal`/`error` con "Cualquier agente" (`bot_id` NULL): ahora se disparan para todos los agentes de su dueño. Antes el hook filtraba por `bot_id` y no las encontraba nunca.
