# Módulo 9 — Alerts (Alertas) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo (sin tests) |
| Avance (alcance original) | 100 % — 10/10 entregables |
| Madurez (estimada) | 50 % — ver [Avance](#avance) |
| Tablas | `alert_rules`, `alert_events` (R/W); `bots`, `signals`, `orders` (R, vía hooks) |
| Depende de | [M1](M01-AUTH.md), [M7](M07-BOTS-SIGNALS.md) y [M8](M08-ORDERS-EXECUTION.md) (hooks); mailer para el canal email |
| Lo usan | Es un consumidor: lo invocan [M7](M07-BOTS-SIGNALS.md) y [M8](M08-ORDERS-EXECUTION.md) |
| Prefijo API | `/api/alert-rules`, `/api/alert-events`, `/api/alerts` |
| Frontend | `frontend/src/modules/alerts` |
| Última revisión | 2026-10-08 |

## Descripción

**En palabras simples:** Es el sistema de notificaciones. Te avisa cuando pasa algo importante, sin que tengas que estar mirando la pantalla todo el tiempo.

**Qué hace:**
- Define **reglas de alerta** personalizables por tipo:
  - `signal` → "Avísame cuando mi bot genere una señal BUY/SELL"
  - `price` → "Avísame si el precio de BTC/USDT baja de $80,000"
  - `pnl` → "Avísame si el P&L del bot baja del -5%"
  - `drawdown` → "Avísame si el drawdown supera el 10%"
  - `error` → "Avísame cuando el bot entre en error"
- Envía las alertas por **4 canales**: Email (SMTP), Telegram (Bot API), Webhook (HTTP POST a URL externa) y Desktop (notificaciones nativas macOS/Windows/Linux con plyer)
- Las alertas se **disparan automáticamente** cuando se genera una señal (M7) o se ejecuta una orden (M8)
- Guarda un historial de todos los eventos de alerta disparados con estado de entrega
- El despacho es **fire-and-forget**: si falla una alerta, no afecta la operación de trading

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/alerts` — Panel del usuario: reglas configuradas (crear/editar en diálogo, activar/desactivar) + historial de alertas recibidas

**Páginas — Administrador (solo admin):**
- `/#/admin/alerts` — Vista admin: todas las reglas y eventos del sistema
- `/#/admin/telegram` — Ver la configuración y probar la conexión con Telegram Bot

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
| El email usa `ALERT_TEMPLATE` del catálogo del mailer (`alert.html`) | Reutiliza el servicio SMTP existente | Plantilla embebida |
| Telegram configurado por entorno (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_DEFAULT_CHAT_ID`) con página admin de prueba | Un único bot y chat del sistema; `TelegramChannel` admite un `chat_id` propio, pero `FireAlertService` hoy no lo pasa (inferido del código) | Token por usuario |
| Notificaciones de escritorio (`plyer`) **opcionales** (`DESKTOP_NOTIFICATIONS_ENABLED=false`) | Solo tiene sentido en desarrollo local | Dependencia obligatoria |
| `admin_required` importado de `role_guard` (no `role_guard(settings.AUTH_ADMIN_ROLE_ID)`) | Convención del proyecto | — |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (10/10) | Dominio, infraestructura, 4 canales, servicios, REST, hooks y UI usuario + admin |
| Madurez | **≈ 50 %** | Funcionalidad 75 · Tests 0 · Seguridad 65 · Operación 60 |

- **Funcionalidad (75):** de los 5 tipos de regla, `EvaluateAlertsService` solo evalúa `signal`, `error` y `price`; **`pnl` y `drawdown` no se evalúan** en ningún sitio. Las reglas `price` solo se evalúan al llamar a `POST /api/alerts/evaluate` (admin, manual): ni el scheduler ni un job periódico lo hacen.
- **Tests (0):** ningún test cubre este módulo.
- **Seguridad (65):** `WebhookChannel` hace `httpx.post(url)` a la URL configurada en la regla **sin validarla**.
- **Operación (60):** el canal Desktop solo notifica en la máquina donde corre el servidor.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | **Validar la URL del webhook** (solo `https`, bloquear IPs privadas/localhost/metadata) para evitar SSRF: hoy cualquier usuario autenticado puede hacer que el servidor envíe un POST a una URL arbitraria | S |
| Alta | Evaluar las reglas `price` de forma periódica (en el ciclo del scheduler de [M2](M02-MARKET-DATA.md)) en vez de solo con el endpoint manual | S |
| Alta | Implementar la evaluación de `pnl` y `drawdown` (usando `positions`, `fills` y `portfolio_snapshots`) | M |
| Media | Tests de `FireAlertService`, `EvaluateAlertsService` y de cada canal con HTTP/SMTP mockeado | M |
| Media | Reintentos y *backoff* para entregas `failed`, y *cooldown* para no repetir la misma alerta de precio en cada ciclo | M |
| Media | Deduplicación / agrupación de alertas (un bot en error no debe generar una alerta por ciclo) | M |
| Baja | Telegram por usuario (cada uno vincula su chat) y plantillas por canal | M |
| Baja | Botón en `/#/admin/alerts` para `POST /api/alerts/evaluate` (hoy solo por API; el front no lo llama) | S |

## Fuera de alcance y pendientes conocidos

- Evaluación de reglas `pnl` y `drawdown`.
- Evaluación automática periódica de reglas `price`.
- Tests unitarios.
- Canales adicionales (SMS, WhatsApp, Slack, Discord).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `alert_rules` | WRITE | Reglas configuradas por usuario/bot |
| `alert_events` | WRITE | Historial de alertas disparadas |
| `bots` | READ (hook) | Para evaluar reglas tipo 'signal'/'error' |
| `signals` | READ (hook) | Datos de la señal para el payload |
| `orders` | READ (hook) | Datos de la orden para el payload |

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

### Canales (`app/modules/alerts/channels/`)
| Archivo | Clase | Canal |
|---------|-------|-------|
| `channel_interface.py` | `NotificationChannel` (Protocol) | Contrato |
| `email_channel.py` | `EmailChannel` | SMTP via MailerService |
| `telegram_channel.py` | `TelegramChannel` | Bot API via httpx |
| `webhook_channel.py` | `WebhookChannel` | HTTP POST via httpx |
| `desktop_channel.py` | `DesktopChannel` | plyer (macOS/Win/Linux) |

### Servicios (`app/modules/alerts/services/`)
| Subdir | Servicios |
|--------|-----------|
| `alert_rules/` | `list_alert_rules_service.py`, `create_alert_rule_service.py`, `update_alert_rule_service.py` |
| `alert_events/` | `list_alert_events_service.py` |
| `evaluation/` | `fire_alert_service.py` (crea evento + despacha), `evaluate_alerts_service.py` (evalúa reglas) |

Provider: `app/modules/alerts/providers/alert_provider.py` → `AlertServiceFactory`, `get_alert_factory()`, `build_evaluate_alerts_service()`

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/alert-rules` | token | Admin ve todas; user ve las suyas |
| POST | `/api/alert-rules` | token | Crea regla de alerta |
| GET | `/api/alert-rules/{id}` | token | Detalle; ownership check |
| PUT | `/api/alert-rules/{id}` | token | Actualiza regla; ownership check |
| DELETE | `/api/alert-rules/{id}` | token | Soft delete (is_active=False) |
| GET | `/api/alert-events` | token | Historial de eventos |
| POST | `/api/alerts/evaluate` | admin | Evaluación manual de reglas tipo price |
| POST | `/api/alerts/test-telegram` | admin | Test de conexión Telegram |

Los routers declaran `prefix="/alert-rules"`, `"/alert-events"`, `"/alerts"`; el `/api` lo añade `app_factory.py` (`settings.API_PREFIX`).

### Frontend (`frontend/src/modules/alerts/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/alerts` | `routes/_app/alerts.lazy.tsx` | `pages/alerts.tsx` (`AlertsPage`) + `components/alert-rule-form-dialog.tsx` + `components/alert-events-table.tsx` |
| `/#/admin/alerts` | `routes/_app/admin/alerts.lazy.tsx` | `pages/admin-alerts.tsx` + `components/alert-events-table.tsx` |
| `/#/admin/telegram` | `routes/_app/admin/telegram.lazy.tsx` | `pages/admin-telegram.tsx` |

- API: `api/alerts.api.ts` (`/alert-rules`, `/alert-events`, `/alerts/test-telegram`); hooks `use-alerts-queries.ts` / `use-alerts-mutations.ts`; etiquetas `lib/alerts-labels.ts`; badges `components/alert-badges.tsx`.
- Activar/desactivar una regla se hace con `PUT /api/alert-rules/{id}` (`is_active`); el front no usa `DELETE` ni `POST /api/alerts/evaluate`.
- Nombres de bot: `useMyBotsQuery` de [M7](M07-BOTS-SIGNALS.md) en páginas de usuario (una petición por cuenta) y `useBotsQuery()` en admin.

### Hooks en otros módulos
- `app/modules/bots/services/signals/generate_signal_service.py` — hook post-commit: `evaluate_alerts.evaluate_signal_alerts()`
- `app/modules/orders/services/orders/create_order_service.py` — hook post-commit: `evaluate_alerts.evaluate_order_alerts()`
- `app/modules/bots/providers/bot_provider.py` — inyecta `build_evaluate_alerts_service(session)` en `generate_signal()`
- `app/modules/orders/providers/order_provider.py` — inyecta `build_evaluate_alerts_service(session)` en `create_order()`

### Settings nuevos (`.env`)
```
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_DEFAULT_CHAT_ID=<chat_id>
DESKTOP_NOTIFICATIONS_ENABLED=false
```

## Gotchas críticos

- `admin_required` se importa de `app.common.security.jwt.role_guard` (NO usar `role_guard(settings.AUTH_ADMIN_ROLE_ID)`)
- `build_evaluate_alerts_service(session)` evita imports circulares entre M7/M8 y M9
- `TYPE_CHECKING` guard en `generate_signal_service.py` y `create_order_service.py` para evitar import circular en runtime
- Los hooks siempre en `try/except pass` — las alertas nunca abortan el flujo de trading
- El email de alerta usa `ALERT_TEMPLATE` desde `app.modules.mailer.domain.mail_template`
- Template HTML en `app/modules/mailer/templates/alert.html`
- `httpx` ya instalado (v0.28.1) — `plyer` opcional para desktop

## Tests

- **No hay tests** para este módulo en `tests/`.
- Recomendado: `FireAlertService` (crea evento + despacha + registra `delivery_status`), `EvaluateAlertsService` (reglas `signal`/`error`/`price`) y los 4 canales con dependencias mockeadas.

## Riesgos

- **SSRF** a través de `WebhookChannel` (URL sin validar).
- Alertas silenciosas: los hooks tragan cualquier excepción (`try/except pass`); si el canal está mal configurado, nadie se entera salvo por `alert_events.delivery_status = failed`.
- Un usuario podría configurar muchas reglas de precio y saturar el endpoint manual o los canales externos (sin límites ni *cooldown*).

## Historial

- **2026-03** — Módulo completado: 4 canales, reglas y eventos, hooks en M7/M8, UI `/alerts`, `/admin/alerts`, `/admin/telegram`, plantilla `ALERT_TEMPLATE`.
- **Dependencias:** `httpx` 0.28.1 ya instalado; `plyer` opcional.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
