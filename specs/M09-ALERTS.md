# Módulo 9 — Alerts (Alertas) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo (sin tests) |
| Avance (alcance original) | 100 % — 10/10 entregables (+ 3 de 2026-10-19: guarda SSRF, endurecimiento de Telegram, Telegram por usuario) |
| Madurez (estimada) | 58 % — ver [Avance](#avance) |
| Tablas | `alert_rules`, `alert_events` (R/W); `bots`, `signals`, `orders`, `accounts` (R, vía hooks y propiedad); `users` (R: `telegram_chat_id`) |
| Depende de | [M1](M01-AUTH.md) (vínculo del chat de Telegram), [M7](M07-BOTS-SIGNALS.md) y [M8](M08-ORDERS-EXECUTION.md) (hooks; Telegram aprueba/rechaza vía `ExecuteSignalService`); mailer para el canal email |
| Lo usan | Es un consumidor: lo invocan [M7](M07-BOTS-SIGNALS.md) (alertas + aviso de señal pendiente), [M8](M08-ORDERS-EXECUTION.md) y el scheduler (polling de Telegram) |
| Prefijo API | `/api/alert-rules`, `/api/alert-events`, `/api/alerts`, `/api/telegram/webhook` |
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
- Guarda un historial de todos los eventos de alerta disparados con estado de entrega
- El despacho es **fire-and-forget**: si falla una alerta, no afecta la operación de trading
- **Telegram por usuario:** cada persona vincula su chat privado; cuando un agente en modo Con aprobación tiene una señal pendiente, le llega un mensaje con los precios y botones **Aprobar** / **Descartar**. La respuesta se procesa por webhook (producción) o polling (desarrollo).

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
| Telegram de **alertas** sigue con el chat del sistema (`TELEGRAM_DEFAULT_CHAT_ID`); el **chat por usuario** se usa para las señales por aprobar | El vínculo por usuario nació para aprobar señales; `FireAlertService` no cambió | Migrar también las alertas (pendiente) |
| Vínculo del chat por enlace `https://t.me/<bot>?start=<código>` de un solo uso (10 min, guardado como SHA-256) — servicio en [M1](M01-AUTH.md) | La persona no copia IDs; el código no queda en claro en BD | Pedir el `chat_id` a mano |
| Aviso de señal pendiente con **botones inline** `sig:a:<id>` / `sig:r:<id>`; "Ver en Trading App" solo si `FRONTEND_URL` empieza por `https://` | Aprobar con un toque; Telegram rechaza botones con enlaces a localhost | Responder con texto ("SI 123") |
| `TelegramUpdateService` solo entiende `/start <código>` y los `callback_data` con formato fijo, solo en **chats privados**; la identidad sale del chat vinculado y la señal debe ser de un agente de ese usuario (también si es admin) | El texto de la persona nunca se interpreta; desde Telegram cada quien decide lo suyo | Comandos libres |
| Tras decidir, se responde con `answerCallbackQuery` y se reescribe el mensaje original con el resultado (`editMessageText`) | Queda claro en el chat qué pasó con la señal | Mandar un mensaje nuevo |
| Textos del bot en `telegram_messages.py` (`DECISION_MESSAGES`, `LINK_MESSAGES`, botones), con números `es-CO` y hora de Bogotá | Igual que `error_messages.py`: los servicios devuelven códigos | Textos dentro de los servicios |
| Tres modos de recibir respuestas (`TELEGRAM_UPDATES_MODE`): `off` · `polling` (el scheduler líder llama `getUpdates`; desarrollo) · `webhook` (Telegram llama `POST /api/telegram/webhook`; producción) | En desarrollo Telegram no puede llamar a localhost | Solo webhook |
| Webhook protegido con `X-Telegram-Bot-Api-Secret-Token` comparado en tiempo constante con `TELEGRAM_WEBHOOK_SECRET`; sin secreto o con otro modo → 404; con secreto correcto → siempre 200 | Solo Telegram puede llamarlo; con otro código Telegram reintenta el mismo update | Endpoint abierto |
| `/api/telegram/webhook` **excluido de la auditoría HTTP** | El cuerpo de `/start` lleva el código de vinculación y mensajes de terceros | Auditarlo con redacción |
| `telegram_provider.py` no se exporta en `providers/__init__.py` y hace imports diferidos de los providers de orders y users | `orders → alerts` (hooks) importa este paquete: un import a nivel de módulo crearía un ciclo | Reorganizar los paquetes |
| El email usa `ALERT_TEMPLATE` del catálogo del mailer (`alert.html`) | Reutiliza el servicio SMTP existente | Plantilla embebida |
| Notificaciones de escritorio (`plyer`) **opcionales** (`DESKTOP_NOTIFICATIONS_ENABLED=false`) | Solo tiene sentido en desarrollo local | Dependencia obligatoria |
| `admin_required` importado de `role_guard` (no `role_guard(settings.AUTH_ADMIN_ROLE_ID)`) | Convención del proyecto | — |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (10/10) | Dominio, infraestructura, 4 canales, servicios, REST, hooks y UI usuario + admin. Además, 3 entregables nuevos (2026-10-19) |
| Madurez | **≈ 58 %** | Funcionalidad 80 · Tests 0 · Seguridad 85 · Operación 65 |

- **Funcionalidad (80):** Telegram por usuario con aprobación de señales por botones. De los 5 tipos de regla, `EvaluateAlertsService` solo evalúa `signal`, `error` y `price`; **`pnl` y `drawdown` no se evalúan** en ningún sitio. Las reglas `price` solo se evalúan con `POST /api/alerts/evaluate` (admin, manual). Las alertas por Telegram siguen yendo al chat del sistema, no al del usuario.
- **Tests (0):** ningún test cubre este módulo (ni `url_guard`, ni `TelegramUpdateService`).
- **Seguridad (85):** guarda SSRF al guardar y al enviar, sin redirects; reglas solo sobre agentes propios; JSON con máximo 20 claves; HTML escapado y token fuera de los logs; webhook de Telegram con secreto. Riesgo residual de *DNS rebinding* entre la resolución y la conexión (ver [Riesgos](#riesgos)).
- **Operación (65):** polling en el scheduler para desarrollo y webhook para producción; el registro del webhook es manual (`setWebhook`). El canal Desktop solo notifica en la máquina del servidor.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Evaluar las reglas `price` de forma periódica (en el ciclo del scheduler de [M2](M02-MARKET-DATA.md)) en vez de solo con el endpoint manual | S |
| Alta | Implementar la evaluación de `pnl` y `drawdown` (usando `positions`, `fills` y `portfolio_snapshots`) | M |
| Media | Tests de `url_guard`, `FireAlertService`, `EvaluateAlertsService`, `TelegramUpdateService` (callbacks, `/start`, chat no vinculado) y de cada canal con HTTP/SMTP mockeado | M |
| Media | Enviar las alertas de Telegram al chat vinculado del dueño de la regla (hoy `TELEGRAM_DEFAULT_CHAT_ID`) | S |
| Media | Reintentos y *backoff* para entregas `failed`, y *cooldown* para no repetir la misma alerta de precio en cada ciclo | M |
| Media | Deduplicación / agrupación de alertas (un bot en error no debe generar una alerta por ciclo) | M |
| Media | Cerrar el *DNS rebinding* del webhook: conectar a la IP ya validada o pasar por un proxy de salida que filtre IPs | M |
| Baja | Persistir el `offset` del polling (hoy en memoria; tras reiniciar Telegram reenvía lo no confirmado ≤ 24 h) | S |
| Baja | Plantillas por canal | M |
| Baja | Botón en `/#/admin/alerts` para `POST /api/alerts/evaluate` (hoy solo por API; el front no lo llama) | S |

## Fuera de alcance y pendientes conocidos

- Evaluación de reglas `pnl` y `drawdown`.
- Evaluación automática periódica de reglas `price`.
- Tests unitarios.
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
| `users` | READ | `telegram_chat_id` del dueño del agente (aviso) y del chat que responde (decisión); columnas de [M1](M01-AUTH.md) |

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
| `telegram_messages.py` | `DECISION_MESSAGES`, `LINK_MESSAGES`, `BUTTON_APPROVE/REJECT/OPEN_APP`, `pending_signal_text(...)`, `decision_text(code)`, `format_number` | Textos del bot (rol notificación) |
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
| `evaluation/` | `fire_alert_service.py` (crea evento + despacha), `evaluate_alerts_service.py` (evalúa reglas) |
| `telegram/` | `signal_approval_notifier.py` (`SignalApprovalNotifier.notify(signal, bot)`: sin token, sin cuenta o sin chat vinculado no envía), `telegram_update_service.py` (`TelegramUpdateService.handle(update)`: `/start <código>` → `TelegramLinkService.confirm`; `sig:a:<id>` / `sig:r:<id>` → `ExecuteSignalService.execute/reject(channel="telegram")`) |

Providers:
- `app/modules/alerts/providers/alert_provider.py` → `AlertServiceFactory`, `get_alert_factory()`, `build_evaluate_alerts_service()`
- `app/modules/alerts/providers/telegram_provider.py` → `build_signal_approval_notifier(session)` (lo usa `BotServiceFactory.generate_signal()`), `build_telegram_update_service(session)` (`None` sin `TELEGRAM_BOT_TOKEN`; lo usan el webhook y el polling)

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/alert-rules` | token | Admin ve todas; user ve las suyas |
| POST | `/api/alert-rules` | token | Crea regla; `bot_id` debe ser un agente propio; webhook https público; `rule_spec`/`channels` ≤ 20 claves |
| GET | `/api/alert-rules/{id}` | token | Detalle; ownership check |
| PUT | `/api/alert-rules/{id}` | token | Actualiza regla; ownership check; webhook validado |
| DELETE | `/api/alert-rules/{id}` | token | Soft delete (is_active=False) |
| GET | `/api/alert-events` | token | Historial de eventos |
| POST | `/api/alerts/evaluate` | admin | Evaluación manual de reglas tipo price |
| POST | `/api/alerts/test-telegram` | admin | Test de conexión Telegram |
| POST | `/api/telegram/webhook` | cabecera `X-Telegram-Bot-Api-Secret-Token` | Updates del bot (solo con `TELEGRAM_UPDATES_MODE=webhook`); fuera de Swagger (`include_in_schema=False`) y de la auditoría |

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

### Hooks en otros módulos
- `app/modules/bots/services/signals/generate_signal_service.py` — hook post-commit: `evaluate_alerts.evaluate_signal_alerts()` y, si la señal queda `pending` en modo `approval`, `notify_pending(signal, bot)`
- `app/modules/orders/services/orders/create_order_service.py` — hook post-commit: `evaluate_alerts.evaluate_order_alerts()` (también tras un rechazo)
- `app/modules/bots/providers/bot_provider.py` — inyecta `build_evaluate_alerts_service(session)` y `build_signal_approval_notifier(session).notify` en `generate_signal()`
- `app/modules/orders/providers/order_provider.py` — inyecta `build_evaluate_alerts_service(session)` en `create_order()`
- `app/modules/scheduler/execution_cycle.py` — `_poll_telegram()` en modo polling

### Settings (`.env`)
```
TELEGRAM_BOT_TOKEN=<token>          # de @BotFather; vacío = Telegram inactivo
TELEGRAM_DEFAULT_CHAT_ID=<chat_id>  # chat de las alertas
TELEGRAM_BOT_USERNAME=              # @usuario del bot sin @ (enlace t.me/<bot>?start=...)
TELEGRAM_UPDATES_MODE=off           # off | polling (desarrollo) | webhook (producción)
TELEGRAM_WEBHOOK_SECRET=            # secret_token de setWebhook; obligatorio con webhook
FRONTEND_URL=http://localhost:5193  # enlaces en Telegram (botón solo si es https)
DESKTOP_NOTIFICATIONS_ENABLED=false
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

- **No hay tests** para este módulo en `tests/`.
- Recomendado: `url_guard` (IPs privadas, IPv4 mapeada, `.internal`, puertos), `FireAlertService` (crea evento + despacha + registra `delivery_status`), `EvaluateAlertsService` (reglas `signal`/`error`/`price`), `TelegramUpdateService` y los canales con dependencias mockeadas.

## Riesgos

- **DNS rebinding:** entre la resolución DNS y la conexión del webhook hay una ventana (TTL 0). Riesgo residual bajo con redirects desactivados; cerrarlo del todo exige un proxy de salida que filtre IPs.
- Alertas silenciosas: los hooks tragan cualquier excepción; si el canal está mal configurado, nadie se entera salvo por `alert_events.delivery_status = failed`.
- Un usuario podría configurar muchas reglas de precio y saturar el endpoint manual o los canales externos (sin límites ni *cooldown*).
- Quien controle el chat de Telegram vinculado puede aprobar las señales de esa cuenta: desvincularlo desde el menú de usuario si se pierde el teléfono.

## Historial

- **2026-03** — Módulo completado: 4 canales, reglas y eventos, hooks en M7/M8, UI `/alerts`, `/admin/alerts`, `/admin/telegram`, plantilla `ALERT_TEMPLATE`.
- **Dependencias:** `httpx` 0.28.1 ya instalado; `plyer` opcional.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-10** — Seed `alerts`: tres reglas demo (señal y drawdown del 5 % del agente de oro, error del agente de BTC), solo canal de escritorio, idempotente por (user_id, name).
- **2026-10-19** — Auditoría de seguridad: guarda SSRF del webhook (`url_guard.py`: https, hosts públicos, resolución DNS al enviar, sin redirects, URL fuera de los logs; `ALERT_RULE_INVALID_WEBHOOK`), reglas solo sobre agentes propios, límite de claves en los JSON; Telegram con HTML escapado, token fuera de los logs y helper `telegram_api`.
- **2026-10-19** — Telegram por usuario para el modo Con aprobación: `SignalApprovalNotifier` (botones `sig:a`/`sig:r`), `TelegramUpdateService`, `TelegramReplier`, `telegram_messages.py`, `telegram_poller.py` (polling en el scheduler), `POST /api/telegram/webhook` con secreto (fuera de la auditoría), `telegram_provider.py`; settings `TELEGRAM_BOT_USERNAME`, `TELEGRAM_UPDATES_MODE`, `TELEGRAM_WEBHOOK_SECRET`, `FRONTEND_URL`.
- **2026-10-20** — Todas las alertas: columna **Dueño** (nombre y correo) y filtro por dueño en Reglas y Eventos; Telegram pasa al grupo admin **Configuración**.
